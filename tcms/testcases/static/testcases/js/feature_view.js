$(document).ready(function() {
    //displayLoadingDiv();
    var table = $("#resultsTable").DataTable({
        ajax: function(data, callback, settings) {
            var params = {};

            if ($('#id_product').val()) {
                product_id = $('#id_product').val();
                params['product'] = $('#id_product').val();
            };

            //if ($('#id_category').val()) {
            //    params['category'] = $('#id_category').val();
            //};
            dataTableJsonRPC('Component.filter_for_view', params, callback);
        },
        columns: [
            { data: "id" },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/admin/management/component/'+ data.id + '/change" target="_parent">' + escapeHTML(data.name) + '</a>';
                }
            },
            { data: "initial_owner" },
            { data: "initial_qa_contact" },
            {
                data: null,
                render: function (data, type, full, meta) {
                    //console.debug(data)
                    //console.debug(data.case_id)
                    var case_link = ''
                    if (data.case_id){
                        data.case_id.forEach(function(element) {
                             case_link = case_link + '<a href="/case/'+ element + '/" target="_parent">' + (element) + ' </a>';
                        })
                    }
                    return case_link;
                }
            },
        ],
        dom: "t",
        language: {
            zeroRecords: "No records found"
        },
        order: [[ 0, 'asc' ]],
        lengthMenu: [[50]],
    });

    hookIntoPagination('#resultsTable', table);

    $('#id_product').change(function() { 
        displayLoadingDiv();
        reloadTableAndPagainfo(table);
    });
    $('#id_add_feature').click(function() {
        var ref_url = '/admin/management/component/add/?product='+product_id;
        window.open(ref_url)
    });
    $('.bootstrap-switch').bootstrapSwitch();

    $('.selectpicker').selectpicker();
});
function reloadTableAndPagainfo(table){
    var updatePage = function() {
        var info = table.page.info();
        $('.total-pages').html(info.pages);
        console.debug("hidden loading")
        hiddenLoadingDiv();
    }
    table.ajax.reload(updatePage);  
    
}
function displayLoadingDiv(){
    var loading_div = document.getElementById("loading_div");
    loading_div.style.display = 'block';
}

function hiddenLoadingDiv(){
    var loading_div = document.getElementById("loading_div");
    loading_div.style.display = 'none';
}