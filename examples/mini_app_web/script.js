const telegram = Telegram.WebApp;
telegram.ready();

class ModifyStyle{ 
  constructor(element) {
    this.element = element;
  };
  disableButton() {
    this.element.style.backgroundColor = 'transparent';
    this.element.style.color = 'var(--tg-theme-button-color)';
    this.element.style.border = "solid 1px var(--tg-theme-button-color)";
  };
  enableButton() {
    this.element.style.backgroundColor = "var(--tg-theme-button-color)";
    this.element.style.color = 'var(--tg-theme-text-color)';
  };
};

class TableModify{
  constructor(element) {
    this.element = element;
  }
  addElements(element_1, element_2) {
    this.element.innerHTML += `<tr id="${element_1}"> <td>  ${element_1} </td> <td> ${element_2} </td> </tr>`;
  }
  removeElement(id) {
    document.getElementById(id).remove();
  }
};

const button = {
  send_message : document.getElementById('send-message-button'),
  back : document.getElementById('back-button'),
  main: document.getElementById('main-button'),
  settings: document.getElementById('settings-button'),
  success: document.getElementById('success-button'),
  warning: document.getElementById('warning-button'),
  error: document.getElementById('error-button'),
  popup: document.getElementById('popup-button'),
  alert: document.getElementById('alert-button'),
  confirm: document.getElementById('confirm-button'),
  contact: document.getElementById('contact-button'),
  write_access: document.getElementById('write-access-button'),
  biometrics: document.getElementById('biometrics-button'),
  cloud_add: document.getElementById('cloud-add-button'),
  cloud_remove: document.getElementById('cloud-remove-button'),
  vertical_scroll_enable: document.getElementById('enable-scroll-button'),
  vertical_scroll_disable: document.getElementById('disable-scroll-button'),
  close_confirm_enable: document.getElementById('enable-close-confirm-button'),
  close_confirm_disable: document.getElementById('disable-close-confirm-button'),
  post_story_photo: document.getElementById('post-story-photo-button'),
  post_story_video: document.getElementById('post-story-video-button'),
  post_story_with_link: document.getElementById('post-story-with-link-button'),
  show_QR: document.getElementById('show-QR-button') ,
  expand: document.getElementById('expand-button'),
  close: document.getElementById('close-button'),
};

const input = {
  message: document.querySelector('.send-message__input'),
  cloud_add_key: document.querySelector('.cloud-storage__input_add-key'),
  cloud_add_value: document.querySelector('.cloud-storage__input_add-value'),
  cloud_remove_key: document.querySelector('.cloud-storage__input_remove'),
};

const text = {
  telegram_link: document.getElementById('telegram-link'),
  internal_link: document.getElementById('internal-link'),
  version: document.getElementById('version-text'),
  platform: document.getElementById('platform-text'),
  color_scheme: document.getElementById('color-scheme-text')
};

const table = {
  cloud_table: document.querySelector(".cloud-storage__table"),
  biometrics_table: document.getElementById("biometrics-table")
}

const colors_tweaks = [
  document.getElementById('header-yellow'),
  document.getElementById('header-button_color'),
  document.getElementById('header-red'),
  document.getElementById('header-default'),
  document.getElementById('background-yellow'),
  document.getElementById('background-button_color'),
  document.getElementById('background-red'),
  document.getElementById('background-default'),
];

telegram.MainButton.setParams({text: 'Close', color: '#ba4d47'});
telegram.MainButton.onClick(() => {telegram.close()});
telegram.MainButton.show();
telegram.enableVerticalSwipes();

telegram.CloudStorage.getKeys((error, keys) => {
  let table_modify = new TableModify(table.cloud_table);
  if (keys.length) {table_modify.removeElement("null-storage-row")};
  keys.forEach((key) => {
    telegram.CloudStorage.getItem(key, (error, item) => {
      table_modify.addElements(key, item)
    });
  });
});

document.getElementById('initDataUnsafe-block').innerHTML += `<pre class="data__text"> ${JSON.stringify(telegram.initDataUnsafe, null, 2)} </pre>`;
document.getElementById('themeParams-block').innerHTML += `<pre class="data__text"> ${JSON.stringify(telegram.themeParams, null, 2)} </pre>`;

let biometrics_table_modify = new TableModify(table.biometrics_table);

telegram.BiometricManager.init(() => {['isInited', 'isBiometricAvailable', 'biometricType', 'isAccessRequested', 'isAccessGranted', 'isBiometricTokenSaved', 'deviceId'].forEach((field) => {
  biometrics_table_modify.addElements(field, eval(`telegram.BiometricManager.${field}`));
}); biometrics_table_modify.removeElement('null-biometrics-row')  });

['themeChanged', 'viewportChanged', 'mainButtonClicked', 'backButtonClicked', 'settingsButtonClicked', 'invoiceClosed', 'popupClosed', 'qrTextReceived', 'scanQrPopupClosed', 
'clipboardTextReceived', 'writeAccessRequested', 'contactRequested', 'biometricManagerUpdated', 'biometricAuthRequested', 'biometricTokenUpdated'].forEach((element) => {
  telegram.onEvent(element, () => {
    document.getElementById('event-block').innerHTML += `<p class="event__text"> ${element} </p>`;
  });
});

text.color_scheme.innerText += telegram.colorScheme;
text.version.innerText += telegram.version;
text.platform.innerText += telegram.platform;

button.send_message.addEventListener('click', () => {
  telegram.sendData(input.message.value);
  if (telegram.initDataUnsafe) telegram.showAlert('SendData only works in miniapp that opened with reply keyboard.')
  input.message.value = ''
});

button.main.addEventListener('click', (e) => {
  const modify_button = new ModifyStyle(e.currentTarget);
  if (e.currentTarget.value == 'enable') {
    e.currentTarget.value = 'disable';
    modify_button.disableButton();
    telegram.MainButton.hide();
  } else {
    e.currentTarget.value = 'enable';
    modify_button.enableButton();
    telegram.MainButton.show();
  }
});

button.back.addEventListener('click', (e) => {
  const modify_button = new ModifyStyle(e.currentTarget);
  if (e.currentTarget.value == 'enable') {
    e.currentTarget.value = 'disable';
    modify_button.disableButton();
    telegram.BackButton.hide();
  } else {
    e.currentTarget.value = 'enable';
    modify_button.enableButton();
    telegram.BackButton.show();
  }
});

button.settings.addEventListener('click', (e) => {
  const modify_button = new ModifyStyle(e.currentTarget);
  if (e.currentTarget.value == 'enable') {
    e.currentTarget.value = 'disable';
    modify_button.disableButton();
    telegram.SettingsButton.hide();
  } else {
    e.currentTarget.value = 'enable';
    modify_button.enableButton();
    telegram.SettingsButton.show();
  }
});

button.success.addEventListener('click', () => {
    telegram.HapticFeedback.notificationOccurred('success');
});

button.warning.addEventListener('click', () => {
    telegram.HapticFeedback.notificationOccurred('warning');
});

button.error.addEventListener('click', () => {
  telegram.HapticFeedback.notificationOccurred('error');
});

button.popup.addEventListener('click', () => {
  telegram.showPopup({title: 'popup', message: 'this is popup message', buttons: [{ text: 'roger'}]});
});

button.alert.addEventListener('click', () => {
    telegram.showAlert('This is alert message');
});

button.confirm.addEventListener('click', () => {
  telegram.showConfirm('This is confirm message');
});

button.contact.addEventListener('click', () => {
  telegram.requestContact();
});

button.write_access.addEventListener('click', () => {
  telegram.requestWriteAccess();
});

button.biometrics.addEventListener('click', () => {
  telegram.BiometricManager.requestAccess({'reseaon': 'this is biometrics request'});
});

button.vertical_scroll_enable.addEventListener('click', (e) => {
  const modify_scroll_enable = new ModifyStyle(e.currentTarget);
  const modify_scroll_disable = new ModifyStyle(button.vertical_scroll_disable);
  if (e.currentTarget.value == 'disable') {
    e.currentTarget.value = 'enable';
    modify_scroll_enable.enableButton();
    modify_scroll_disable.disableButton();
    button.vertical_scroll_disable.value = 'disable';
    telegram.enableVerticalSwipes();
  }; 
});

button.vertical_scroll_disable.addEventListener('click', (e) => {
  const modify_scroll_disable = new ModifyStyle(e.currentTarget);
  const modify_scroll_enable = new ModifyStyle(button.vertical_scroll_enable);
  if (e.currentTarget.value == 'disable') {
    e.currentTarget.value = 'enable';
    modify_scroll_disable.enableButton();
    modify_scroll_enable.disableButton();
    telegram.disableVerticalSwipes();
    button.vertical_scroll_enable.value = 'disable';
  }; 
});

button.close_confirm_enable.addEventListener('click', (e) => {
  const modify_close_confirm_enable = new ModifyStyle(e.currentTarget);
  const modify_close_confirm_disable = new ModifyStyle(button.close_confirm_disable);
  if (e.currentTarget.value == 'disable') {
    e.currentTarget.value = 'enable';
    modify_close_confirm_enable.enableButton();
    modify_close_confirm_disable.disableButton();
    button.close_confirm_disable.value = 'disable';
    telegram.enableClosingConfirmation();
  }; 
});

button.close_confirm_disable.addEventListener('click', (e) => {
  const modify_close_confirm_disable= new ModifyStyle(e.currentTarget);
  const modify_close_confirm_enable= new ModifyStyle(button.close_confirm_enable);
  if (e.currentTarget.value == 'disable') {
    e.currentTarget.id = 'enable';
    modify_close_confirm_enable.disableButton();
    modify_close_confirm_disable.enableButton();
    button.close_confirm_enable.value = 'disable';
    telegram.disableClosingConfirmation();
  }; 
});

button.show_QR.addEventListener('click', () => {
  telegram.showScanQrPopup({text: "this is QR scanner"});
});

button.expand.addEventListener('click', () => {
  telegram.expand();
});

button.close.addEventListener('click', () => {
  telegram.close();
});

button.cloud_add.addEventListener('click', () => {
  let table_modify = new TableModify(table.cloud_table);
  telegram.CloudStorage.setItem(input.cloud_add_key.value, input.cloud_add_value.value, (error, is_stored) => {
    if (!is_stored) telegram.showAlert(error);
    else {
        table_modify.addElements(input.cloud_add_key.value, input.cloud_add_value.value);
        new TableModify(table.cloud_table).removeElement('null-storage-row');
    };
    input.cloud_add_key.value = '';
    input.cloud_add_value.value = '';
  });
});

button.cloud_remove.addEventListener('click', () => {
  let table_modify = new TableModify(table.cloud_table);
  telegram.CloudStorage.removeItem(input.cloud_remove_key.value, (error, is_removed) => {
    if (!is_removed) telegram.showAlert(error);
    else table_modify.removeElement(input.cloud_remove_key.value);
    input.cloud_remove_key.value = '';
  });
});

button.post_story_photo.addEventListener('click', () => {
  telegram.shareToStory('https://telegra.ph/file/e194a37aed103485469b4.jpg', {text: 'This is photo story'});
});

button.post_story_video.addEventListener('click', () => {
  telegram.shareToStory('https://telegra.ph/file/16ffd9385a017b59f458e.mp4', {text: 'This is video story'});
});

button.post_story_with_link.addEventListener('click', () => {
  telegram.shareToStory('https://telegra.ph/file/e194a37aed103485469b4.jpg', {text: 'This is story with link', widget_link: {url: 'https://t.me/joinchat/Bn4ixj84FIZVkwhk2jag6A'}}); 
});

colors_tweaks.forEach((element) => {
  element.addEventListener('click', (e) => {
    const color = window.getComputedStyle(e.currentTarget).backgroundColor;
    if (e.currentTarget.id.includes('header')){
      telegram.setHeaderColor(color);
    } else {
      telegram.setBackgroundColor(color);
      document.querySelector('.body').style.backgroundColor = telegram.backgroundColor;
    };
  });
});

text.telegram_link.addEventListener('click', () => {
  telegram.openTelegramLink("https://t.me/joinchat/Bn4ixj84FIZVkwhk2jag6A");
});

text.internal_link.addEventListener('click', () => {
  telegram.openLink('https://telegram.org', {try_instant_view: false});
});
