$(document).ready(function() {
    select_node = '';
    var table = $("#resultsTable").DataTable({
        ajax: function(data, callback, settings) {
            var params = {};

            if (($('#id_suite').val() != "")) {
                //params['category__suite__product'] = $('#id_product').val();
                params['category__suite'] = $('#id_suite').val();
                if (select_node != 0){
                    params['category'] = select_node;
                }
                console.debug($('#id_product').val())
                dataTableJsonRPC('TestCase.filter', params, callback);
            }            
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
    });

    hookIntoPagination('#resultsTable', table);
    $('#id_add_category').click(function() {
        var ref_url = '/admin/testcases/category/add/?parent_category='+select_node+'&suite='+suite_id;
        console.debug(ref_url)
        //window.location.href = ref_url;
        window.open(ref_url)
    });
    $('#btn_newcase').click(function() {
        var ref_url = '/cases/new/?category='+select_node+'&suite='+suite_id+'&product='+product_id;
        console.debug(ref_url)
        //window.location.href = ref_url;
        window.open(ref_url)
    });
    $('#id_delte_category').click(function() {
        window.location.href = '/admin/testcases/category/'+select_node+'/delete';
    });
    var updateSuite = function(data) {
            updateSelectWithPicker(data, '#id_suite', 'id', 'name');
    }
//
    $('#id_product').change(function() {
        product_id = $(this).val();
        console.debug(product_id)
        if (product_id) {
            jsonRPC('Suite.filter', {product: product_id}, updateSuite);
        } else {
            updateSuite([]);
        }
    });
    product_id = $('#id_product').val();
    console.debug(product_id)
    if (product_id) {
        jsonRPC('Suite.filter', {product: product_id}, updateSuite);
    } else {
        updateSuite([]);
    }
    $('#id_suite').change(function() {
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
                node.parent_id = element.parent_category_id;
                node_list.push(node)
            })

            treedata = node_list.filter(function(element) {
                //return (element.parent_id == default_id && element.id != default_id);
                return (element.parent_id == null)
            });
            console.debug(treedata)
            addSubNode(treedata,node_list);
            console.debug(treedata)
            //tree = $('#tree').treeview({    
            //    data: treedata, 
            //    collapseIcon: "fa fa-angle-down",
            //    expandIcon: "fa fa-angle-right",
            //    nodeIcon: "fa fa-folder",
            //    showCheckbox: false,
            //    onNodeSelected: function(event, data){
            //        select_node = data.id;
            //        reloadTableAndPagainfo(table);
            //    }
            //});
            $('#tree').jstree({
              'core' : {
                'data' : treedata
              }
            });
            $('#tree').jstree("refresh")

            $('#tree').on("select_node.jstree", function (e, data) {
              console.log("The selected nodes are:");
              console.log(data.node.id);
              select_node = data.node.id;
              displayLoadingDiv(); 
              reloadTableAndPagainfo(table);
              hiddenLoadingDiv();
            });
            hiddenLoadingDiv();
            
        }

        suite_id = $(this).val();
        //console.debug(product_id)
        if (suite_id) {
            //jsonRPC('Category.filter', {product: product_id}, updateCategory);
            jsonRPC('Category.filter', {suite: suite_id}, genTreeView);
        } else {
            //updateCategory([]);
            hiddenLoadingDiv();
        }
        reloadTableAndPagainfo(table);

    });

    $('.bootstrap-switch').bootstrapSwitch();
  
    $('.selectpicker').selectpicker();


});
function reloadTableAndPagainfo(table){
    var updatePage = function() {
        var info = table.page.info();
        $('.total-pages').html(info.pages);
        //hiddenLoadingDiv();
    }
    console.debug("reload table")
    table.ajax.reload(updatePage);  
    
}

function displayLoadingDiv(){
    var loading_div = document.getElementById("loading_div");
    loading_div.style.display = 'block';
}

function hiddenLoadingDiv(){
    var loading_div = document.getElementById("loading_div");
    console.debug("hidden loading");
    loading_div.style.display = 'none';
}

function addSubNode(treedata,tlist){
    if ((Number(treedata) == 0)||(Number(tlist) == 0)){
        return 1;
    }   
    treedata.forEach(function(item,index) {
        sub_list = tlist.filter(function(element) {
            return (item.id == element.parent_id);
        });
        if (Number(sub_list) == 0){
            return 1;
        }
        //item.nodes = sub_list;
        item.children = sub_list;
        return addSubNode(item.children,tlist);
        //return addSubNode(item.nodes,tlist);
    });
}
