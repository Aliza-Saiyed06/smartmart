/*
 * billing.js  (plain JavaScript, no jQuery)
 *
 * The cart lives in the browser as an array of objects:
 *     { id: 3, name: 'Milk', price: 3200, stock: 20, quantity: 2 }
 * Prices are stored in PAISE (whole numbers) so there are no floating-point
 * errors such as 0.1 + 0.2 = 0.30000000000000004.
 *
 * On "Generate Bill" only product ids and quantities are sent to the server.
 * The server reads the real prices from the database.
 */

document.addEventListener('DOMContentLoaded', function () {

    var cart = [];
    var messageTimer = null;

    var productTable = document.getElementById('billing-product-table');
    var searchBox = document.getElementById('product-search');
    var billingForm = document.getElementById('billing-form');
    var cartBody = document.getElementById('cart-body');
    var cartMessage = document.getElementById('cart-message');
    var cartCount = document.getElementById('cart-count');
    var cartUnits = document.getElementById('cart-units');
    var cartTotal = document.getElementById('cart-total');
    var cartDataField = document.getElementById('cart-data');
    var generateButton = document.getElementById('generate-bill-btn');

    // ---------- Small helpers ----------

    function toPaise(rupees) {
        return Math.round(parseFloat(rupees) * 100);
    }

    function formatRupees(paise) {
        return '\u20B9' + (paise / 100).toFixed(2);     // \u20B9 is the rupee sign
    }

    // Creates an element with optional CSS classes and text
    function makeElement(tag, className, text) {
        var element = document.createElement(tag);
        if (className) {
            element.className = className;
        }
        if (text !== undefined) {
            element.textContent = text;
        }
        return element;
    }

    // Shows a Bootstrap alert above the cart for 4 seconds
    function showMessage(text, type) {
        cartMessage.innerHTML = '';
        cartMessage.appendChild(makeElement('div', 'alert alert-' + type + ' py-2 mx-3 mt-3 mb-0 small', text));
        clearTimeout(messageTimer);
        messageTimer = setTimeout(function () {
            cartMessage.innerHTML = '';
        }, 4000);
    }

    function findItem(productId) {
        for (var i = 0; i < cart.length; i++) {
            if (cart[i].id === productId) {
                return cart[i];
            }
        }
        return null;
    }

    // ---------- Cart actions ----------

    function addToCart(productId, name, price, stock) {
        var item = findItem(productId);

        if (item) {
            if (item.quantity >= item.stock) {
                showMessage('Only ' + item.stock + ' unit(s) of ' + item.name + ' in stock.', 'warning');
                return;
            }
            item.quantity += 1;
        } else {
            if (stock < 1) {
                showMessage(name + ' is out of stock.', 'danger');
                return;
            }
            cart.push({ id: productId, name: name, price: price, stock: stock, quantity: 1 });
        }
        renderCart();
    }

    function addProductFromRow(row) {
        addToCart(
            parseInt(row.dataset.productId, 10),
            row.dataset.name,
            toPaise(row.dataset.price),
            parseInt(row.dataset.stock, 10)
        );
    }

    // Called when the cashier types a quantity directly
    function setQuantity(productId, typedValue) {
        var item = findItem(productId);
        var quantity = parseInt(typedValue, 10);

        if (isNaN(quantity) || quantity < 1) {
            item.quantity = 1;
            showMessage('Quantity must be a whole number of at least 1.', 'warning');
        } else if (quantity > item.stock) {
            item.quantity = item.stock;
            showMessage('Only ' + item.stock + ' unit(s) of ' + item.name + ' in stock.', 'warning');
        } else {
            item.quantity = quantity;
        }
        renderCart();
    }

    function removeItem(productId) {
        cart = cart.filter(function (item) {
            return item.id !== productId;
        });
        renderCart();
    }

    // ---------- Drawing the cart ----------

    // Builds the  [-] [ 2 ] [+]  control for one cart line
    function makeQuantityControl(item) {
        var group = makeElement('div', 'input-group input-group-sm qty-group');

        var minusButton = makeElement('button', 'btn btn-outline-secondary', '\u2212');
        minusButton.type = 'button';
        minusButton.disabled = item.quantity <= 1;
        minusButton.setAttribute('aria-label', 'Decrease quantity of ' + item.name);
        minusButton.addEventListener('click', function () {
            item.quantity -= 1;
            renderCart();
        });

        var input = makeElement('input', 'form-control text-center qty-input');
        input.type = 'number';
        input.min = 1;
        input.max = item.stock;
        input.value = item.quantity;
        input.setAttribute('aria-label', 'Quantity of ' + item.name);
        input.addEventListener('change', function () {
            setQuantity(item.id, input.value);
        });
        // Enter in this box must NOT submit the bill by accident
        input.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                input.blur();                 // triggers the 'change' event above
            }
        });

        var plusButton = makeElement('button', 'btn btn-outline-secondary', '+');
        plusButton.type = 'button';
        plusButton.disabled = item.quantity >= item.stock;
        plusButton.setAttribute('aria-label', 'Increase quantity of ' + item.name);
        plusButton.addEventListener('click', function () {
            item.quantity += 1;
            renderCart();
        });

        group.appendChild(minusButton);
        group.appendChild(input);
        group.appendChild(plusButton);
        return group;
    }

    // Redraws the whole cart table and the totals
    function renderCart() {
        cartBody.innerHTML = '';
        var totalPaise = 0;
        var totalUnits = 0;

        if (cart.length === 0) {
            var emptyRow = makeElement('tr');
            var emptyCell = makeElement('td', 'text-center text-muted py-4', 'Cart is empty. Click "Add" on a product.');
            emptyCell.colSpan = 4;
            emptyRow.appendChild(emptyCell);
            cartBody.appendChild(emptyRow);
        }

        cart.forEach(function (item) {
            var lineTotal = item.price * item.quantity;
            totalPaise += lineTotal;
            totalUnits += item.quantity;

            var row = makeElement('tr');

            var nameCell = makeElement('td');
            nameCell.appendChild(makeElement('div', 'fw-semibold', item.name));
            nameCell.appendChild(makeElement('div', 'small text-muted', formatRupees(item.price) + ' each'));
            row.appendChild(nameCell);

            var quantityCell = makeElement('td');
            quantityCell.appendChild(makeQuantityControl(item));
            row.appendChild(quantityCell);

            row.appendChild(makeElement('td', 'text-end fw-semibold', formatRupees(lineTotal)));

            var removeCell = makeElement('td', 'text-end');
            var removeButton = makeElement('button', 'btn btn-sm btn-outline-danger');
            removeButton.type = 'button';
            removeButton.setAttribute('aria-label', 'Remove ' + item.name);
            removeButton.appendChild(makeElement('i', 'bi bi-trash'));
            removeButton.addEventListener('click', function () {
                removeItem(item.id);
            });
            removeCell.appendChild(removeButton);
            row.appendChild(removeCell);

            cartBody.appendChild(row);
        });

        cartCount.textContent = cart.length;
        cartUnits.textContent = totalUnits;
        cartTotal.textContent = formatRupees(totalPaise);
    }

    // ---------- Product list interactions ----------

    if (productTable) {
        // One click listener for the whole table (event delegation)
        productTable.addEventListener('click', function (event) {
            var button = event.target.closest('.add-to-cart-btn');
            if (button && !button.disabled) {
                addProductFromRow(button.closest('tr'));
            }
        });
    }

    // Pressing Enter in the search box adds the first visible, in-stock product.
    // (This is how a barcode scanner would behave, so it is cashier-friendly.)
    if (searchBox && productTable) {
        searchBox.addEventListener('keydown', function (event) {
            if (event.key !== 'Enter') {
                return;
            }
            event.preventDefault();

            var rows = productTable.querySelectorAll('tbody tr[data-product-id]');
            for (var i = 0; i < rows.length; i++) {
                var isVisible = rows[i].style.display !== 'none';       // jQuery hides rows with inline style
                var inStock = parseInt(rows[i].dataset.stock, 10) > 0;
                if (isVisible && inStock) {
                    addProductFromRow(rows[i]);
                    searchBox.value = '';
                    searchBox.dispatchEvent(new Event('input', { bubbles: true }));   // tells filters.js to refresh
                    searchBox.focus();
                    return;
                }
            }
            showMessage('No in-stock product matches your search.', 'warning');
        });
    }

    // ---------- Submitting the bill ----------

    billingForm.addEventListener('submit', function (event) {
        if (cart.length === 0) {
            event.preventDefault();
            showMessage('The cart is empty. Add at least one product.', 'warning');
            return;
        }

        // Send only ids and quantities. The server looks up the real prices.
        var simpleCart = cart.map(function (item) {
            return { product_id: item.id, quantity: item.quantity };
        });
        cartDataField.value = JSON.stringify(simpleCart);

        // Stop a double-click from creating two bills
        generateButton.disabled = true;
        generateButton.textContent = 'Generating...';
    });

    // If the browser restores this page from its back/forward cache, reload it
    // so the stock numbers and the button are fresh.
    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            window.location.reload();
        }
    });

    // ---------- Restore the cart after a failed bill ----------

    var savedElement = document.getElementById('saved-items');
    if (savedElement && productTable) {
        var savedItems = JSON.parse(savedElement.textContent);
        savedItems.forEach(function (saved) {
            var row = productTable.querySelector('tr[data-product-id="' + saved.product_id + '"]');
            if (!row) {
                return;                                       // product was deleted meanwhile
            }
            var stock = parseInt(row.dataset.stock, 10);      // fresh stock from the database
            var quantity = Math.min(saved.quantity, stock);
            if (quantity >= 1) {
                cart.push({
                    id: saved.product_id,
                    name: row.dataset.name,
                    price: toPaise(row.dataset.price),
                    stock: stock,
                    quantity: quantity
                });
            }
        });
    }

    renderCart();
});