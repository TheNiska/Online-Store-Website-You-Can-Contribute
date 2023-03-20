// Обработчик клика на кнопку изменения количества продукта
$('.update-quantity').click(function(event) {
  event.preventDefault();
  var form = $(this).closest('form'); // находим ближайшую форму-родителя
  var productId = form.find('input[name="product_id"]').val();
  var category = form.find('input[name="category_name"]').val();
  var quantity = form.find('input[name="quantity"]').val();
  var saleDate = form.find('input[name="sale_date"]').val();
  var action = $(this).val();

  // Отправляем POST-запрос на сервер
  $.ajax({
    url: '/update_quantity/' + productId,
    method: 'POST',
    data: {
      category_name: category,
      action: action,
      sale_date: saleDate,
      quantity: quantity
    },
    success: function(response) {
      // Обновляем содержимое страницы
      var quantity = response.quantity_tmp
      $('#quantity-' + productId).text(quantity);
      alert('Количество товара успешно обновлено');
    },
    error: function(xhr, status, error) {
      alert('Произошла ошибка при обновлении количества товара');
    }
  });
});


// Обработчик клика на кнопку удаления продукта
$('.delete-button').click(function(event) {
    event.preventDefault();
    var form = $(this).closest('form');
    var productId = form.find('input[name="product_id"]').val();
    var button = $(this)

    // Отправляем POST-запрос на сервер
    $.ajax({
      url: '/delete_product/' + productId,
      method: 'POST',
      dataType: 'json', 

      success: function(response) {
        // Обновляем содержимое страницы
        var tr = button.closest('tr');
        tr.remove()
        alert('Товар удален');
      },
      error: function(xhr, status, error) {
        alert('Произошла ошибка при удалении товара');
      }
    });
});