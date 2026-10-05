/*
 * validation.js  (plain JavaScript, no jQuery)
 *
 * CLIENT-SIDE validation: runs in the browser BEFORE the form is sent.
 * Gives instant feedback, but a user can bypass it, so Django ALSO validates
 * everything on the server (forms.py). Both layers are needed.
 *
 * It reads the rules from the HTML attributes of each field:
 *   required         -> field cannot be empty
 *   min / max        -> number limits
 *   type="email"     -> must look like an email address
 *   pattern="..."    -> must match a regular expression
 *   data-integer     -> whole numbers only
 *   data-no-past     -> a date field that cannot be before today
 *   data-label       -> field name used in messages
 *   data-pattern-message -> custom message for a failed pattern
 */

document.addEventListener('DOMContentLoaded', function () {

    var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    // Today's date as YYYY-MM-DD (the same format a date input uses)
    function todayAsString() {
        var now = new Date();
        var month = String(now.getMonth() + 1).padStart(2, '0');
        var day = String(now.getDate()).padStart(2, '0');
        return now.getFullYear() + '-' + month + '-' + day;
    }

    // Returns an error message for one field, or '' if the field is valid.
    function getErrorMessage(field) {
        var label = field.getAttribute('data-label') || 'This field';
        var value = field.value.trim();

        if (field.required && value === '') {
            return label + ' is required.';
        }
        if (value === '') {
            return '';   // optional field left empty: nothing to check
        }

        if (field.type === 'number') {
            var number = Number(value);
            if (isNaN(number)) {
                return label + ' must be a number.';
            }
            if (field.hasAttribute('data-integer') && !/^\d+$/.test(value)) {
                return label + ' must be a whole number (0 or more).';
            }
            if (field.min !== '' && number < Number(field.min)) {
                return label + ' must be at least ' + field.min + '.';
            }
            if (field.max !== '' && number > Number(field.max)) {
                return label + ' must be at most ' + field.max + '.';
            }
        }

        if (field.type === 'email' && !emailPattern.test(value)) {
            return 'Please enter a valid email address.';
        }

        if (field.hasAttribute('pattern')) {
            var regex = new RegExp('^(?:' + field.getAttribute('pattern') + ')$');
            if (!regex.test(value)) {
                return field.getAttribute('data-pattern-message') || label + ' has an invalid format.';
            }
        }

        if (field.type === 'date' && field.hasAttribute('data-no-past') && value < todayAsString()) {
            return label + ' cannot be in the past.';
        }

        return '';
    }

    // Shows or clears the red error text under a field.
    function showError(field, message) {
        var box = field.parentElement.querySelector('.invalid-feedback');
        if (!box) {
            box = document.createElement('div');
            box.className = 'invalid-feedback';
            field.insertAdjacentElement('afterend', box);
        }
        box.textContent = message;
        field.classList.toggle('is-invalid', message !== '');
    }

    function validateField(field) {
        var message = getErrorMessage(field);
        showError(field, message);
        return message === '';
    }

    // Validates all fields of a form. Returns true only if every field is valid.
    function validateForm(form) {
        var allValid = true;
        form.querySelectorAll('input, select, textarea').forEach(function (field) {
            if (field.type === 'hidden' || field.type === 'submit') {
                return;
            }
            if (!validateField(field)) {
                allValid = false;
            }
        });
        return allValid;
    }

    document.querySelectorAll('form.js-validate').forEach(function (form) {

        // When the user clicks Save: stop the form if something is invalid
        form.addEventListener('submit', function (event) {
            if (!validateForm(form)) {
                event.preventDefault();
                var firstInvalid = form.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
        });

        form.querySelectorAll('input, select, textarea').forEach(function (field) {
            // Check a field when the user leaves it
            field.addEventListener('blur', function () {
                validateField(field);
            });
            // If the field was already red, re-check it while the user fixes it
            field.addEventListener('input', function () {
                if (field.classList.contains('is-invalid')) {
                    validateField(field);
                }
            });
        });
    });
});