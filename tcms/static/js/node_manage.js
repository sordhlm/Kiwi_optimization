$(document).ready(function() {
    console.debug("start JS")
    //var editor  = require( 'datatables.net-editor' )();
    //freshNodeData();
    gen_parent_table(nodes)
    //freshNodeData();
    var tg = window.setInterval("freshNodeData()",10000);//N毫秒刷新一次，1000毫秒＝1秒
    //$("#btn_up").click(function(){
    //    Add(reloadWindow);
    //});
    $('#id_add_node').click(function() {
        var ref_url = '/admin/management/node/add/';
        console.debug(ref_url)
        //window.location.href = ref_url;
        window.open(ref_url)
    });
    $('#ParentTable').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var siteTable = $('#ParentTable').DataTable()
        var row = siteTable.row( tr );
        console.log("ParentTable click", row)
        var td = ($(this).closest('td'))
        if ( row.child.isShown() ) {
            // This row is already open - close it
            destroyChild(row);
            tr.removeClass('shown');
        }
        else {
            // Open this row
            createChild(row, gen_detail_table); // class is for background colour
            tr.addClass('shown');
        }
    } ); 

});
function freshNodeData() {
    //console.debug("refresh status")
    updateNode(update_table);
}
function updateNode(callback) {
    jQ.ajax({
        'url': '/run/update_nodes/',
        'type': 'POST',
        'data': [],
        'success': function (data, textStatus, jqXHR) {
            //console.debug(data)
            callback(data.result);
            //console.debug(data)
        },
        'error': function (jqXHR, textStatus, errorThrown) {
            //alert("false");
            console.debug("Node Update failed");
        }
    });
}
function update_table(table_data){
    var siteTable = $('#ParentTable').DataTable()
    //var rows = siteTable.rows()
    //console.log("table rows", rows)
    //console.log("ajax data", table_data)
    //siteTable.rows().iterator( 'row', function ( context, index ) {
    table_data.forEach(function(val, index){
        //console.log("table row", this.row( index ).data())
        //console.debug(index, val)
        var id = "id_" + val.id;
        //elements = $('#ParentTable').find('strong#'+id);
        //console.debug("tag id: ", id)
        var label = document.getElementById(id);  
        //console.log(elements)
        if(label){
            old_stat = 'node-state-'+label.innerText
            label.innerText = val.state;
            //elements.append(this.row( index ).data().state)
            //console.log(elements)
            $('#'+id).parent().parent().removeClass( old_stat );
            $('#'+id).parent().parent().addClass( 'node-state-'+ val.state );
        }
    } );
}
function gen_parent_table(table_data){
    console.debug('gen_parent_table: ',table_data)
    if (table_data.length){
        var groupColumn = 4;
        var siteTable = $('#ParentTable').DataTable( {
            order: [ groupColumn, 'asc' ],
            data: table_data,
            columns: [  
                {
                    className: 'details-control',
                    orderable: false,
                    data: null,
                    defaultContent: '',
                    width: '5%'
                },         
                //{ data: 'name' },
                {
                    data: null,
                    render: function (data, type, full, meta) {
                        return '<a href="/admin/management/node/'+ data.id + '/change/" target="_parent">' + (data.name) + '</a>';
                    }
                },
                { data: 'ip'},
                { data: 'os'},
                //{ data: 'project'},
                {
                    data: null,
                    visible: false,
                    render: function (data, type, full, meta) {
                        return '<a href="/admin/management/product/'+ data.product_id + '/change/" target="_parent">' + (data.product) + '</a>';
                    }
                },
                { data: 'vendor'},
                { data: 'fw'},
                //{ data: 'state'},
                {
                    data: null,
                    render: function (data, type, full, meta) {
                        return '<strong id="id_'+data.id+'">' + (data.state) + '</strong>';
                    }
                },
                { data: 'tag', width: '15%',},
                { data: 'description'}, 
            ],
            columnDefs: [
            {
                "targets": [8],
                "sClass":"cls_tag",
                createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
                    $(cell).click(function () {
                        //$(this).html('<input type="text" size="16" style="width: 100%"/>');
                        //var aInput = $(this).find(":input");
                        //aInput.focus().val(cellData);
                        //console.debug('before add input', this.innerText)
                        var old_txt = this.innerText
                        $(this).html('<input type="text" size="16" style="width: 100%"/>');
                        //console.debug(cell)
                        var aInput = $(this).find(":input");
                        //aInput.focus(function(){
                        //    aInput.val(cellData);
                        //});
                        //console.debug('after add input', this.innerText)
                        //console.debug('click cell', cellData)
                        //aInput.val(old_txt)
                        aInput.focus().val(old_txt)
                        //console.debug(cellData)
                        //aInput.val(cellData);
                    });
                    $(cell).on("blur", ":input", function () {
                        //var ret = window.confirm("Are you sure to update Tag, this will directly update database and can't be undo.")
                        //if(ret == true){
                            var text = $(this).val();
                            $(cell).html(text);
                            //console.debug('cell on', text)
                            //console.debug(rowData)
                            console.debug('blur', text)
                            update_tag(rowData, 'tag', text)
                            siteTable.cell(cell).data(text)
                        //}
                    })
                }
            },
            //{
            //    "targets": [9],
            //    createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
            //        $(cell).click(function () {
            //            $(this).html('<input type="text" size="16" style="width: 100%"/>');
            //            var aInput = $(this).find(":input");
            //            aInput.focus().val(cellData);
            //        });
            //        $(cell).on("blur", ":input", function () {
            //            var text = $(this).val();
            //            $(cell).html(text);
            //            console.debug(text)
            //            console.debug(rowData)
            //            update_tag(rowData, 'description', text)
            //            siteTable.cell(cell).data(text)
            //        })
            //    }
            //},
            ],
            //aoColumnDefs:[
            //    {"sClass":"cls_tag","aTargets":[8]}
            //],
            select: {
                toggleable: false
            },
            dom: "t",
            destroy: true,
            scrollX:        true,
            paging:         false,
            drawCallback: function ( settings ) {
                var api = this.api();
                var rows = api.rows( {page:'current'} ).nodes();
                var last=null;
                //console.debug("group callback", rows)
                api.column(groupColumn, {page:'current'} ).data().each( function ( data, i ) {
                    //console.debug("group callback", data)
                    group = data.product
                    if ( last !== group ) {
                        $(rows).eq( i ).before(
                            '<tr class="group"><td colspan="9">'+group+'</td></tr>'
                        );
                        last = group;
                    }
                } );
            }
        } );
        update_table(table_data)
        $('input.gn-search').on( 'keyup click', function () {
            filterGlobal();
        } );
        //document.getElementById("id_perf_result").style.display = "block";
        //SeleteResultFromInputList(table_data)
    }
}
function filterGlobal () {
    $('#ParentTable').DataTable().search(
        $('.gn-search').val(),
    ).draw();
}
function createChild ( row, callback ) {
    // This is the table we'll convert into a DataTable
    var table = $('<table class="display_childtable table-hover" width="100%"/>');
    
    // Display it the child row
    row.child( table ).show();
 
    // Initialise as a DataTable
    query_result(row.data(), table, callback)
    //var usersTable = table.DataTable( {
        // ...
    //} );
}

function destroyChild(row) {
    var table = $("table", row.child());
    //delete_and_update_chart(table.DataTable().rows(".selected").data())
    //table.detach();
    table.DataTable().destroy();
    
    // And then hide the row
    row.child.hide();
    document.getElementById("id_history_container").style.display = "none";
}
function query_result(group, table, callback){
  console.debug("query_result",group)
  //keys = serializeResultFromInputList_li(li, 'gn-li-selected')
  $.ajax({
      'url': '/run/get_test_detail/',
      'type': 'POST',
      'data': {'ip':group.ip},
      'success': function (data, textStatus, jqXHR) {
          console.debug("query_result return data",data.detail)
          callback(data, table)
      },
      'error': function (jqXHR, textStatus, errorThrown) {
          alert("ajax error");
      }
  });
}
function update_tag(row, key, txt){
  //keys = serializeResultFromInputList_li(li, 'gn-li-selected')
  $.ajax({
      'url': '/run/update_tag/',
      'type': 'POST',
      'data': {'ip':row.ip, 'text':txt, 'key':key},
      'success': function (data, textStatus, jqXHR) {
          console.debug("update_tag pass")
      },
      'error': function (jqXHR, textStatus, errorThrown) {
          alert("update tag fail");
      }
  });
}
function gen_detail_table(table_data, table_container){
    //var table_data = []
    console.debug("gen_table detail", table_data.detail)
    console.debug("gen_table usage", table_data.usage)
    var groupColumn = 3
    var table = table_container.DataTable({
        data: table_data.usage,
        columns: [
            { title: 'date', data: "date" },
            //{ title: 'usage', data: "usage"},
            { title: 'total_time(h)', data: "total_time" },
            {
                title: 'busy',
                data: null,
                render: function (data, type, full, meta) {
                    return '<strong>' + (data.busy+" %") + '</strong>';
                }
            },
            {
                title: 'Detail',
                data: null,
                render: function (data, type, full, meta) {
                    //return '<strong id="id_'+data.id+'">' + (data.state) + '</strong>';
                    return '<div class="progress"> \
                    <div class="progress-bar progress-passed" style="width:'+ data.busy +'%;"></div>\
                    <div class="progress-bar progress-failed" style="width: '+ data.idle +'%"></div>\
                    </div>'
                }
            },
        ],
        dom: "t",
        //fixedHeader:{
        //    header: false,
        //},
        select: {
            toggleable: true,
            //items:'cell'
        },
        scrollY:        200,
        scrollX:        true,
        paging:         false
    });
    $('#historyTable').DataTable( {
        order: [ 1, 'asc' ],
        data: table_data.detail,
        columns: [      
            { data: 'name'},
            { data: 'start_time'},
            { data: 'duration'},
            //{ data: 'state_txt'},
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<strong class="test-status-'+data.state_txt+'">' + (data.state_txt) + '</strong>';
                }
            },
        ],
        select: {
            toggleable: false
        },
        dom: "Brti",
        destroy: true,
    } );
    document.getElementById("id_history_container").style.display = "block";
}