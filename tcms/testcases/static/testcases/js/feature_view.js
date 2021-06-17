$(document).ready(function() {
    //displayLoadingDiv();
    select_node = 0;
    var table = $("#resultsTable").DataTable({
        ajax: function(data, callback, settings) {
            var params = {};

            if ($('#id_product').val()) {
                product_id = $('#id_product').val();
                params['product'] = $('#id_product').val();
            };
            if (select_node != 0){
                    params['component'] = select_node;
                }
            //if ($('#id_category').val()) {
            //    params['category'] = $('#id_category').val();
            //};
            //dataTableJsonRPC('Component.filter_for_view', params, callback);
            dataTableJsonRPC('Component.filter_testcases', params, callback);
        },
        columns: [
            { data: "case_id" },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/case/'+ data.case_id + '/" target="_parent">' + escapeHTML(data.summary) + '</a>';
                }
            },
            { data: "author" },
            
            { data: "is_automated" },
            { data: "case_status"},
            { data: "category"},
            { data: "priority" },
            { data: "create_date"},
        ],
        dom: "t",
        language: {
            zeroRecords: "No records found"
        },
        order: [[ 0, 'asc' ]],
        lengthMenu: [[50]],
    });
    $('#id_product').change(function() {
        displayLoadingDiv(); 
        select_node = 0;
        var genTreeView = function(data) {
            var treedata = [];
            var node_list = [];
            var max_depth = 10;
            var default_id = 0;
            data.forEach(function(element) {
                //var node = {text:"",nodes:[],id:0,parent_id:0};
                var node = {text:"",children:[],id:0,parent_id:0};
                node.text = element.name;
                node.id = element.id;
                //node.parent_id = element.parent_category_id;
                node_list.push(node)
            })

            //treedata = node_list.filter(function(element) {
                //return (element.parent_id == default_id && element.id != default_id);
            //    return (element.parent_id == null)
            //});
            $('#tree').jstree({
              'plugins': ['types','themes','contextmenu'],
              'core' : {
                'data' : node_list
              },
              'contextmenu':{
                select_node:true,
                show_at_node:true,
                items:{
                    "Edit":{  
                        "label":"Edit",  
                        //"icon": "glyphicon glyphicon-plus",
                        "action":function(data){
                            var ref_url = '/admin/management/component/'+select_node+'/change/';
                            console.debug(ref_url)
                            window.open(ref_url)
                        } 
                    },
                    "Add":{  
                        "label":"Add",  
                        //"icon": "glyphicon glyphicon-plus",
                        "action":function(data){
                            var ref_url = '/admin/management/component/add/?product='+product_id;
                            window.open(ref_url)
                        } 
                    },
                    "delete":{  
                        "label":"Delete",  
                        //"icon": "glyphicon glyphicon-plus",
                        "action":function(data){
                            var ref_url = '/admin/management/component/'+select_node+'/delete';
                            window.open(ref_url)
                        } 
                    },
                }
              }
            });
            $('#tree').on("select_node.jstree", function (e, data) {
              console.log("The selected nodes are:");
              console.log(data.node.id);
              select_node = data.node.id;
              displayLoadingDiv(); 
              reloadTableAndPagainfo(table);
            });
            
        }

        product_id = $(this).val();
        if (product_id) {
            //jsonRPC('Category.filter', {product: product_id}, updateCategory);
            jsonRPC('Component.filter', {product: product_id}, genTreeView);
        } else {
            //updateCategory([]);
            hiddenLoadingDiv();
        }
        reloadTableAndPagainfo(table);

    });
    $('#id_add_category').click(function() {
        var ref_url = '/admin/management/component/add/';
        console.debug(ref_url)
        //window.location.href = ref_url;
        window.open(ref_url)
    });
    $('#id_delte_category').click(function() {
        window.location.href = '/admin/management/component/'+select_node+'/delete';
    });
    hookIntoPagination('#resultsTable', table);

    //$('#id_product').change(function() { 
    //    displayLoadingDiv();
    //    reloadTableAndPagainfo(table);
    //});
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