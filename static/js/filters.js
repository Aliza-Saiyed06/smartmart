/*
 * filters.js  (jQuery)
 *
 * Live search and filtering for tables. No page reload.
 *
 * How to use it in a template:
 *   1. Give the table an id:                  <table id="product-table">
 *   2. Give every row a data-search attribute: <tr data-search="milk dairy sumul">
 *      (and e.g. data-status="LOW_STOCK" for dropdown filters)
 *   3. Search box:      <input class="live-search" data-table="#product-table">
 *   4. Dropdown filter: <select class="live-filter" data-table="#product-table" data-field="status">
 *      (compares the dropdown value with the row's data-status attribute)
 *   5. Optional: a row with class "no-results-row" is shown when nothing matches,
 *      and <span class="filter-count" data-table="#product-table"> shows the number of visible rows.
 */

$(document).ready(function () {

    // Re-checks every row of one table against the search box and dropdowns.
    function applyFilters(tableSelector) {
        var table = $(tableSelector);
        var filters = $('.live-filter[data-table="' + tableSelector + '"]');

        var searchText = $('.live-search[data-table="' + tableSelector + '"]').val() || '';
        searchText = searchText.toLowerCase().trim();

        var visibleRows = 0;

        table.find('tbody tr[data-search]').each(function () {
            var row = $(this);

            // 1. Does the row's text contain what the user typed?
            var showRow = row.attr('data-search').indexOf(searchText) !== -1;

            // 2. Does the row match every dropdown filter?
            filters.each(function () {
                var wantedValue = $(this).val();
                var field = $(this).attr('data-field');
                if (wantedValue !== '' && row.attr('data-' + field) !== wantedValue) {
                    showRow = false;
                }
            });

            row.toggle(showRow);       // show or hide the row (DOM manipulation)
            if (showRow) {
                visibleRows++;
            }
        });

        table.find('.no-results-row').toggle(visibleRows === 0);
        $('.filter-count[data-table="' + tableSelector + '"]').text(visibleRows);
    }

    // Run the filter whenever the user types or changes a dropdown
    $('.live-search, .live-filter').on('input change', function () {
        applyFilters($(this).attr('data-table'));
    });

    // A dropdown with class "auto-submit" submits its form as soon as it changes
    // (used for the category filter, which is filtered on the server)
    $('select.auto-submit').on('change', function () {
        $(this).closest('form').submit();
    });
});