// web/telegram_mini_app.js
@override
void initState() {
  super.initState();
  _initializeBackButton();
}

void _initializeBackButton() {
  // Инициализация кнопки "Назад"
  js.context.callMethod('eval', ["""
    var BackButton = WebApp.BackButton;
    BackButton.show();
    BackButton.onClick(function() {
      WebApp.showAlert("Нет пути назад!");
      BackButton.hide();
    });
    WebApp.onEvent('backButtonClicked', function() {
      // Ваш код здесь
    });
  """]);
}

@override
void dispose() {
  // Скрытие кнопки "Назад" при уничтожении виджета
  js.context.callMethod('eval', ["""
    var BackButton = WebApp.BackButton;
    BackButton.hide();
  """]);
  super.dispose();
}
