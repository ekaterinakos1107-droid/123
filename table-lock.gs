/**
 * Монопольная блокировка Google Таблицы.
 *
 * Один человек нажимает "Занять таблицу" — остальные на это время
 * не могут ничего изменить (таблица у них становится только для чтения).
 * После "Освободить таблицу" или по истечении таймаута доступ возвращается всем.
 */

const LOCK_TAG      = 'EXCLUSIVE_LOCK';
const LOCK_MINUTES  = 30;   // на сколько минут таблица занимается
const EXTEND_MINUTES = 30;  // на сколько продлевается кнопкой "Продлить"

/* ---------- меню ---------- */

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🔒 Блокировка')
    .addItem('Занять таблицу',      'lockTable')
    .addItem('Продлить',            'extendLock')
    .addItem('Освободить таблицу',  'unlockTable')
    .addSeparator()
    .addItem('Кто сейчас редактирует?', 'whoHasLock')
    .addToUi();
}

/* ---------- основные действия ---------- */

function lockTable() {
  const ui = SpreadsheetApp.getUi();
  const me = currentUser_();
  const holder = props_().getProperty('lock_holder');
  const until  = Number(props_().getProperty('lock_until') || 0);

  if (holder && holder !== me && Date.now() < until) {
    ui.alert('Таблица занята: ' + holder +
             '\nАвтоматически освободится в ' + fmt_(until) + '.');
    return;
  }

  const newUntil = Date.now() + LOCK_MINUTES * 60 * 1000;
  applyProtection_(me, newUntil);
  props_().setProperties({ lock_holder: me, lock_until: String(newUntil) });

  ui.alert('Таблица занята вами до ' + fmt_(newUntil) + '.\n' +
           'Остальные участники сейчас могут только смотреть.\n' +
           'Не забудьте нажать "Освободить таблицу", когда закончите.');
}

function extendLock() {
  const ui = SpreadsheetApp.getUi();
  const me = currentUser_();
  if (props_().getProperty('lock_holder') !== me) {
    ui.alert('Таблица занята не вами.');
    return;
  }
  const newUntil = Date.now() + EXTEND_MINUTES * 60 * 1000;
  applyProtection_(me, newUntil);
  props_().setProperty('lock_until', String(newUntil));
  ui.alert('Продлено до ' + fmt_(newUntil) + '.');
}

function unlockTable() {
  const ui = SpreadsheetApp.getUi();
  const me = currentUser_();
  const holder = props_().getProperty('lock_holder');
  const isOwner = me === SpreadsheetApp.getActiveSpreadsheet().getOwner().getEmail();

  if (holder && holder !== me && !isOwner) {
    ui.alert('Таблицу занял ' + holder + '. Снять блокировку может только он или владелец файла.');
    return;
  }
  releaseLock_();
  ui.alert('Таблица свободна — редактировать могут все.');
}

function whoHasLock() {
  const holder = props_().getProperty('lock_holder');
  const until  = Number(props_().getProperty('lock_until') || 0);
  const msg = (holder && Date.now() < until)
    ? 'Сейчас редактирует: ' + holder + '\nДо ' + fmt_(until)
    : 'Таблица свободна.';
  SpreadsheetApp.getUi().alert(msg);
}

/* ---------- автоснятие блокировки ---------- */

/** Запустить один раз вручную — создаёт проверку раз в 5 минут. */
function installTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'autoRelease') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('autoRelease').timeBased().everyMinutes(5).create();
}

function autoRelease() {
  const until = Number(props_().getProperty('lock_until') || 0);
  if (until && Date.now() > until) releaseLock_();
}

/* ---------- внутреннее ---------- */

function props_() {
  return PropertiesService.getDocumentProperties();
}

function currentUser_() {
  return Session.getActiveUser().getEmail() ||
         Session.getEffectiveUser().getEmail() ||
         'неизвестный пользователь';
}

function fmt_(ms) {
  return Utilities.formatDate(new Date(ms),
    SpreadsheetApp.getActiveSpreadsheet().getSpreadsheetTimeZone(), 'HH:mm');
}

function applyProtection_(me, until) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const desc = LOCK_TAG + ' | редактирует ' + me + ' до ' + fmt_(until);

  removeOurProtections_(ss);

  ss.getSheets().forEach(function (sheet) {
    const p = sheet.protect().setDescription(desc);
    p.addEditor(me);
    try { p.setDomainEdit(false); } catch (e) {}   // недоступно для личных аккаунтов
    p.getEditors().forEach(function (user) {
      const email = user.getEmail();
      if (email && email !== me) {
        try { p.removeEditor(email); } catch (e) {} // владельца файла исключить нельзя
      }
    });
  });
}

function releaseLock_() {
  removeOurProtections_(SpreadsheetApp.getActiveSpreadsheet());
  props_().deleteProperty('lock_holder');
  props_().deleteProperty('lock_until');
}

function removeOurProtections_(ss) {
  [SpreadsheetApp.ProtectionType.SHEET, SpreadsheetApp.ProtectionType.RANGE].forEach(function (type) {
    ss.getSheets().forEach(function (sheet) {
      sheet.getProtections(type).forEach(function (p) {
        if ((p.getDescription() || '').indexOf(LOCK_TAG) === 0) p.remove();
      });
    });
  });
}
