$(document).ready(function() {
    $('.btnBlueCaserun').mouseover(function() {
      $(this).find('ul').show();
    }).mouseout(function() {
      $(this).find('ul').hide();
    });

    
    var genTreegrid = function(data) {  
        var columns = [
                       {
                        "title":"Summary",
                        "field":"name"
                       },
                       {
                        "title":"ID",
                        "field":"id"
                       },
                       {
                        "title":"Author",
                        "field":"auth"
                       },    
                       {
                        "title":"Priority",
                        "field":"priority"
                       },                   
                     ];
        var cate_columns = [
                       {
                        "title":"Summary",
                        "field":"name"
                       },
                       {
                        "title":"Author",
                        "field":"auth"
                       },    
                       {
                        "title":"Priority",
                        "field":"priority"
                       },                   
                     ];
        var target = $("#id_tree_table");
        $('thead').remove()
        $('tbody').remove()

        var thr = $('<tr></tr>');
        
        var th = $('<th class="nosort" align="left" width="30px"></th>');
        var span = $('<input id="id_check_tree_all_button" type="checkbox"/>');
        th.append(span);
        thr.append(th)
        
        $.each(columns, function (i, item) {
            var th = $('<th style="padding:10px;"></th>');
            th.text(item.title);
            thr.append(th);
        });
        var thead = $('<thead></thead>');
        thead.append(thr);
        target.append(thead);
        //构造表体
        var tbody = $('<tbody></tbody>');
        console.debug(data);
        $.each(data, function (i, item) {
            if (item.depth == 0){
                var tr = $('<tr id='+item.id+' class="category collapsed"></tr>');
                var td = $('<td></td>');
                var span = $('<input class="category" type="checkbox" name="cate" value="'+item.id+'">');
                tr.append(td);
                td.append(span)
                var td = $('<td></td>');
                var span = $('<span></span>');
                span.addClass('icon node-icon fa fa-folder')
                td.addClass('treegrid-node');
                tr.append(td);
                td.append(span)
                span.text(" "+item.name);
                $.each(cate_columns, function (i, column) {
                    if(i != 0){
                        var td = $('<td></td>');
                        td.text(item[column.field]);
                        tr.append(td);
                    }
                });
            }
            else if(item.isCate){
                var tr = $('<tr id='+item.id+' class="category " data-parent=#'+(item.pid)+'></tr>');
                var td = $('<td></td>');
                var span = $('<input class="category" type="checkbox" name="cate" value="'+item.id+'">');
                tr.append(td);
                td.append(span)
                var td = $('<td></td>');
                var span = $('<span></span>');
                span.addClass('icon node-icon fa fa-folder')
                td.addClass('treegrid-node');
                td.append(span)
                span.text(" "+item.name);
                tr.append(td);
                $.each(cate_columns, function (i, column) {
                    if(i != 0){
                        var td = $('<td></td>');
                        td.text(item[column.field]);
                        tr.append(td);
                    }
                });

            }
            else{
                var tr = $('<tr class="case" data-parent=#'+(item.pid)+'></tr>');
                var td = $('<td></td>');
                var span = $('<input id="'+item.pid+'" type="checkbox" name="treecase" value="'+item.id+'">');
                tr.append(td);
                td.append(span)
                var td = $('<td></td>');
                var span = $('<span></span>');
                span.addClass('icon node-icon fa fa-folder')
                td.addClass('treegrid-node');
                td.append(span)
                span.text(" "+item.name);
                tr.append(td);
                $.each(columns, function (i, column) {
                    if(i != 0){
                        if (column.field == "id"){
                            var td = $('<td></td>');
                            //td.text(item[column.field]);
                            var ref = $('<a href="/case/'+item[column.field]+'"></a>');
                            ref.text(item[column.field])
                            td.append(ref)
                            tr.append(td);
                        }
                        else{
                            var td = $('<td></td>');
                            td.text(item[column.field]);
                            tr.append(td);
                        }
                    }
                });
            }         
            tbody.append(tr);
                       
        });
        target.append(tbody);
        jQ('#id_tree_table').treegrid({initialState:'collapsed'});
        if (jQ('#id_check_tree_all_button').length) {
            jQ('#id_check_tree_all_button').bind('click', function(e) {
                toggleAllTreeCheckBoxes(this, 'id_tree_table', 'treecase');
            });
        }
        if (jQ('.category').length) {
            jQ('.category').bind('click', function(e) {
                toggleSubCheckBoxes(this, 'id_tree_table', 'treecase');
            });
        }
        hiddenLoadingDiv();
    }
    
    jQ('ul.suiteList a').click(function() {
        var suite_id = jQ(this).attr('value');
        if (suite_id == '') {
            return false;
        }
        displayLoadingDiv();
        jsonRPC('TestCase.assigncase', [plan_id, suite_id], genTreegrid);
    }); 
});
function displayLoadingDiv(){
    var loading_div = document.getElementById("loading_div");
    loading_div.style.display = 'block';
}

function hiddenLoadingDiv(){
    var loading_div = document.getElementById("loading_div");
    loading_div.style.display = 'none';
}
function toggleAllSubCategory(element, container, arr){ 
    var cate_id = element.value;
    var sub_list = []
    //console.debug(element.value);
    arr.push(element.value)
    //if (element.checked) {
    //  jQ('#' + container).parent().find('input[name="' + name + '"][id="'+element.value+'"]').not(':disabled').attr('checked', true);
    //} else {
    //  jQ('#' + container).parent().find('input[name="'+ name + '"][id="'+element.value+'"]').not(':disabled').attr('checked', false);
    //}
    sub_list = jQ('#' + container).parent().find('tr[data-parent=#'+cate_id+'][class^="category"]').find('input')
    if (sub_list.length){
        for(var i = 0; i < sub_list.length; i++){
            var item = sub_list.get(i)
            toggleAllSubCategory(item, container, arr)
        }
    }
}

function toggleAllTreeCheckBoxes(element, container, name) {
    if (element.checked) {
      jQ('#' + container).parent().find('input[name="' + name + '"]').not(':disabled').attr('checked', true);
    } else {
      jQ('#' + container).parent().find('input[name="'+ name + '"]').not(':disabled').attr('checked', false);
    }
}

function toggleSubCheckBoxes(element, container, name) {
    var arr = [];
    toggleAllSubCategory(element, container, arr)
    //console.debug(arr)
    if (arr.length){
        for(var i = 0; i < arr.length; i++){
            if (element.checked) {
              jQ('#' + container).parent().find('input[name="' + name + '"][id="'+arr[i]+'"]').not(':disabled').attr('checked', true);
            } else {
              jQ('#' + container).parent().find('input[name="'+ name + '"][id="'+arr[i]+'"]').not(':disabled').attr('checked', false);
            }            
        }
    }
}