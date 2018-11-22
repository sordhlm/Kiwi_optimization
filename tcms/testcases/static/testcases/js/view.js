$(document).ready(function() {
    select_node = '';
    var table = $("#resultsTable").DataTable({
        ajax: function(data, callback, settings) {
            var params = {};

            if ($('#id_product').val()) {
                params['category__product'] = $('#id_product').val();
                if (select_node != 0){
                    params['category'] = select_node;
                }
            };

            //if ($('#id_category').val()) {
            //    params['category'] = $('#id_category').val();
            //};
            console.log(params['category'])
            dataTableJsonRPC('TestCase.filter', params, callback);
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
            { data: "default_tester" },
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

    $('#btn_newcase').click(function() {
        window.location.href = '/cases/new';
    });
    $('#btn_test').click(function() {
        window.location.href = '/admin/testcases/category/add';
        alert("done");
        var node = $('#tree').treeview('getSelected');
        add ={text: ""};
        add.text = prompt("Please input section name","")
        if (add.text){
            $('#tree').treeview('addNode',[add,node]);
        }
    });
    $('#id_product').change(function() {
        var updateCategory = function(data) {
            updateSelect(data, '#id_category', 'id', 'name');
        }

        var genTreeView = function(data) {
            var treedata = [];
            var node_list = [];
            var max_parent = 1;
            data.forEach(function(element) {
                var node = {text:"",nodes:[],id:0,parent_id:0};
                node.text = element.name;
                node.id = element.id;
                node.parent_id = element.parent_category_id;
                node_list.push(node)
                if(node.parent_id > max_parent){
                    max_parent = node.parent_id;
                }
            })
            treedata = node_list.filter(function(element) {
                return (element.parent_id == 1 && element.id != 1);
            });
            if (max_parent > 1){
                for(var i = 2;i <= max_parent; i++){
                    sub_list = node_list.filter(function(element) {
                        return (element.parent_id == i);
                    });
                    if (Number(sub_list) != 0){
                        sub_list.forEach(function(element){
                            addSubNode(treedata,element);
                        });
                    }
                }
            }

            tree = $('#tree').treeview({    
                data: treedata, 
                collapseIcon: "fa fa-angle-down",
                expandIcon: "fa fa-angle-right",
                nodeIcon: "fa fa-folder",
                showCheckbox: false,
                onNodeSelected: function(event, data){
                    select_node = data.id;
                    table.ajax.reload();
                }
            });
        }

        var product_id = $(this).val();
        if (product_id) {
            jsonRPC('Category.filter', {product: product_id}, updateCategory);
            jsonRPC('Category.filter', {product: product_id}, genTreeView);
        } else {
            updateCategory([]);
        }
        table.ajax.reload();
    });
    $('#id_category').change(function() {
        table.ajax.reload();
    });

    $('.bootstrap-switch').bootstrapSwitch();

    $('.selectpicker').selectpicker();
});
function addSubNode(list,node){
    if (Number(list) == 0){
        return 1;
    }
    list.forEach(function(element,index) {
        if(element.id == node.parent_id){
            element.nodes.push(node)
            return 0;
        }
        return addSubNode(element.nodes,node)
    });
}

