$(document).ready(function() {
    var chart_data = [];
    var chart_obj = {};
    var data_type_list = []
    var data_for_chart = [];
    var qos_table_col = 0;
    var confirm = 2;
    
    var chart = new CanvasJS.Chart("bandwidth_chart", {
        theme: "light2",
        //animationEnabled: true,
        zoomEnabled: true,
        title: {
            text: "SSD Performance"
        },
        toolTip: {
            shared: true
        },
        axisX: {
            valueFormatString: "####",
            title: "Time",
        },
        axisY: [
            {
                title: "Bandwidth",
                suffix: "MB/s",
            },
            {
                title: "IOPS",
            },
            {
                title: "Temperate",
                suffix: "C",
            },
        ],

        legend: {
            cursor: "pointer",
            fontSize: 16,
            itemclick: toggleDataSeries
        },    
        data: data_for_chart
    });

    console.debug(tree_data)
    $('#result_tree').jstree({
        'core' : {
          'data' : tree_data
        },
        "types" : {
          "#" : {
            "max_children" : 1,
            "max_depth" : 4,
            "valid_children" : ["root"]
          },
          "root" : {
            "icon" : "/static/3.3.9/assets/images/tree_icon.png",
            "valid_children" : ["default"]
          },
          "default" : {
            "valid_children" : ["default","file"]
          },
          "file" : {
            "icon" : "glyphicon glyphicon-file",
            "valid_children" : []
          }
        },
        "plugins" : [
          "contextmenu", "search", "checkbox",
          "state", "types",
        ],
        "checkbox": {
            "keep_selected_style": false,//是否默认选中
            "three_state": true,//父子级别级联选择
            "tie_selection": false
        },
    });
    //$('#result_tree').on("click.jstree", function (e, data) {
    $('#result_tree').on("check_node.jstree", function (e, data) {
        var ref = $('#result_tree').jstree(true);
        var nodes = ref.get_checked(false);  //使用get_checked方法
        console.log("click jstree", nodes);
        query_group(nodes, 0);
        console.debug("chart data after reload new group: ",chart_data)
    });
    $('#result_tree').on("uncheck_node.jstree", function (e, data) {
        var ref = $('#result_tree').jstree(true);
        var nodes = ref.get_checked(false);  //使用get_checked方法
        console.log("click jstree", nodes);
        query_group(nodes, 0);
        console.debug("chart data after reload new group: ",chart_data)
    });

    axiY_index_table = {
        "write_bw": 0,
        "read_bw": 0,
        "write_iops": 1,
        "read_iops": 1,
        "temperate": 2,
    }
    //console.debug(groups)
    gen_parent_table(groups)
    Object.defineProperties(chart_obj, {
        list:{
            configurable: true,
            get: function(){
                console.log("get: ", list);
                return list
            },
            set: function(val){
                list = val;
                console.log("set: ", val);
                chart_update(val);
            }
        }
    })
    $(".btn-primary").each(function(i) {
        data_type_list.push(this.value);
    });    

    $('[data-toggle="tooltip"]').tooltip()
    $(".gn-search").bind("input propertychange",function(){
        var v = $(this).val();
        $('#result_tree').jstree(true).search(v);
      //var option = $(this).val();
      //var re = new RegExp(option)
      //$(".gn-li").each(function(index) {
      //  str = $(this).text()
      //  console.log(str)
      //  if (re.test(str)) {
      //      this.style.display = "block";
      //  } else {
      //      this.style.display = "none";
      //  }
      //});    
    });
    $("#confirm_btn").click(function(){
        //console.debug($(this).first().innerText)
        var ref_url = window.location.search;
        console.debug(ref_url)
        var m = ref_url.match(/confirm=(\d)/)
        console.debug(m)
        if (m){
            var confirm = (m[1]+1)%3;
        }
        var ref_url = '/report/performance/?confirm='+confirm; 
        window.location.replace(ref_url)  
        console.debug(ref_url)
    });
    $("#delete_btn").click(function(){
        //console.debug($(this).first().innerText)
        var ref = $('#result_tree').jstree(true);
        var nodes = ref.get_checked(false);  //使用get_checked方法
        console.log("delete data", nodes);
        var r = window.confirm('Are you sure you to delete performance result?')
        if (r == true){
            console.log("confirm delete")
            query_group(nodes, 1);
        }
        else{
            console.log("cancel delete")
        }
    });
    $('button.toggle-vis').on( 'click', function (e) {
        e.preventDefault();
        var li = $(this)
        console.debug(li.attr('data-column'))
        // Get the column API object
        var table_container = $('.display_childtable');
        console.debug(table_container)
        if(table_container.length != 0){
            table_container.each(function(index) {
                table = $(this).DataTable()
                console.debug(table)
                var column = table.column( li.attr('data-column') );
                column.visible( ! column.visible() );
            }); 
            if (li.hasClass("btn-danger")){
                console.debug("btn-danger")
                li.removeClass("btn-danger");
                li.addClass("btn-default")
            } else {
                console.debug("btn-default")
                li.removeClass("btn-default");
                li.addClass("btn-danger")
            }
        }
    } );
    new gnMenu( document.getElementById( 'gn-menu' ) );
    $('#ParentTable').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var siteTable = $('#ParentTable').DataTable()
        var row = siteTable.row( tr );
        console.log("ParentTable click", row)
        if ( row.child.isShown() ) {
            // This row is already open - close it
            destroyChild(row);
            tr.removeClass('shown');
        }
        else {
            // Open this row
            createChild(row); // class is for background colour
            tr.addClass('shown');
        }
    } ); 
    //$('#ParentTable').on('click', 'td.delete_col', function () {
    //    var tr = $(this).closest('tr');
    //    var siteTable = $('#ParentTable').DataTable()
    //    var row = siteTable.row( tr );
    //    console.log("ParentTable delete click", row.data())
    //    
    //    var r = window.confirm('Are you sure you to delete performance result: ' + row.data().name)
    //    if (r == true){
    //        console.log("confirm delete")
    //    }
    //    else{
    //        console.log("cancel delete")
    //    }
    //} ); 
    $("button.btn_chart").click(function(){
        var li = $(this)
        console.debug(data_type_list)

        if (li.hasClass("btn-primary")){
            console.debug("btn-primary")
            li.removeClass("btn-primary");
            li.addClass("btn-default")
            pro_data_type(li[0].value, 0)
        } else {
            console.debug("btn-default")
            li.removeClass("btn-default");
            li.addClass("btn-primary")
            pro_data_type(li[0].value, 1)
        }
        trigger_chart_update(chart_data);
    });
    //jQ("#resultsTable").find("tbody").find("tr").bind("click", function(){
    //    var td_id = jQ(this).find("td.sorting_1")[0]
    //    console.debug(td_id.textContent)
    //});

    function chart_update(data){
        console.log("chart_update ...", data)
        if(data){
            data_for_chart = gen_char_data(data)
            console.log("chart_update before render", data_for_chart)
            chart.options.data = data_for_chart;
            chart.render();
            update_qos_table(data)
        }
        hiddenLoadingDiv()
    } 
    function toggleDataSeries(e) {
        if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
            e.dataSeries.visible = false;
        } else {
            e.dataSeries.visible = true;
        }
        e.chart.render();
    }
    function findChartIndex(id){
        for (var i = 0; i < chart_data.length; i++) {
            if (id == chart_data[i].index) return i;
        }   
        return -1;
    }
    function pro_data_type(type, mode){
        console.log("pro_data_type",data_type_list,type,mode)
        if(mode == 0){
            for (var i = 0; i < data_type_list.length; i++) {
                if (type == data_type_list[i]) {
                    data_type_list.splice(i, 1);
                    return 1;
                }
            }   
        }
        else{
            data_type_list.push(type)
        }
    }
    function gen_char_data(data){
        var ret = []
        console.log("gen_char_data:", data)
        for (var i = 0;i < data.length; i++){
            console.log("gen_char_data:", data[i])
            for (var j = 0; j < data_type_list.length; j++) {
                var element = {}
                element = {
                    type: "line",
                    name: data[i].group_name + ": " + data[i].name + " " + data_type_list[j],
                    axisYIndex: axiY_index_table[data_type_list[j]],
                    showInLegend: true,
                    dataPoints: gen_data_point(data[i], data_type_list[j])
                }
                ret.push(element)
            }
        }
        return ret
    }
    function trigger_chart_update(data){
        chart_obj.list = data;
    }
    function query_detail(para, sdata){
      console.log("query_detail before", para)
      $.ajax({
        'url': '/report/query_perf_detail/',
        'type': 'POST',
        'data': para,
        'success': function (data, textStatus, jqXHR) {
          console.debug('result: ', data.result)
          //for(var i = 0; i < data.result.length; i++){
          //  sdata.push(data.result[i])
          //}
          if(data.ok){
            console.debug("query_detail, before update ", sdata)
            console.debug("query_detail, before update return data", data)
            sdata = chart_data_update(sdata, data)
            console.debug("query_detail, after update ", sdata)
            trigger_chart_update(sdata);
          }
          else{
            alert("Get Detail fail");
            hiddenLoadingDiv()
          }
          //gen_chart(data.result)
        },
        'error': function (jqXHR, textStatus, errorThrown) {
          alert("ajax error");
        }
      });
    }
    function gen_table(table_data, table_container){
        //var table_data = []
        console.debug("gen_table", table_data)
        if(table_data.length === 0){
            document.getElementById("id_perf_result").style.display = "none";
            return;
        }
        var groupColumn = 3
        cols = serializeResultFromInputList_button('btn-for-latency', 'btn-danger')
        console.debug(cols)
        hide_cols = [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]
        console.debug(whatleft(hide_cols, cols))
        var table = table_container.DataTable({
            data: table_data,
            columns: [
                { title: 'index', data: "index" },
                { title: 'Name', data: "name"},
                { title: 'BS', data: "configuration.blocksize" },
                { title: 'Duration', data: "duration"},
                { title: 'sTime', data: "start_time"},
                { title: 'WR_BW KiB/s', data: "summary_report.bw_write"},
                { title: 'WR_LAT us', data: "summary_report.avg_latency_write"},
                { title: 'WR_LAT99', data: "summary_report.percent_99_write"},
                { title: 'WR_LAT999', data: "summary_report.percent_999_write"},
                { title: 'WR_LAT9999', data: "summary_report.percent_9999_write"},
                { title: 'WR_LAT99999', data: "summary_report.percent_99999_write"},
                { title: 'WR_LAT999999', data: "summary_report.percent_999999_write"},
                { title: 'WR_LAT9999999', data: "summary_report.percent_9999999_write"},
                { title: 'WR_LAT99999999', data: "summary_report.percent_99999999_write"},
                { title: 'WR_LAT_Max', data: "summary_report.max_latency_write"},
                { title: 'RD_BW KiB/s', data: "summary_report.bw_read"},
                { title: 'RD_LAT us', data: "summary_report.avg_latency_read"},
                { title: 'RD_LAT99', data: "summary_report.percent_99_read"},
                { title: 'RD_LAT999', data: "summary_report.percent_999_read"},
                { title: 'RD_LAT9999', data: "summary_report.percent_9999_read"},
                { title: 'RD_LAT99999', data: "summary_report.percent_99999_read"},
                { title: 'RD_LAT999999', data: "summary_report.percent_999999_read"},
                { title: 'RD_LAT9999999', data: "summary_report.percent_9999999_read"},
                { title: 'RD_LAT99999999', data: "summary_report.percent_99999999_read"},
                { title: 'RD_LAT_Max', data: "summary_report.max_latency_read"},
            ],
            columnDefs: [
                {
                    "targets": whatleft(hide_cols, cols),
                    "visible": false,
                    "searchable": false
                },
            ],
            dom: "t",
            select: {
                toggleable: true,
                //items:'cell'
            },
            scrollY:        200,
            scrollX:        true,
            paging:         false
        });
        table_container.on( 'click', 'tr', function () {
            console.log("click child table", this)
            var table = $(this).parent().parent().DataTable()
            var data = table.row(this).data()
            console.log("click table", data)
            if (data){
                $(this).toggleClass('selected');
                if ($(this).hasClass('selected')) {
                    console.debug("table selected", data)
                    displayLoadingDiv()
                    document.getElementById("id_chart_result").style.display = "block";
                    query_detail(data, chart_data)
                } else {
                    console.debug("table unselected", data)
                    delete_and_update_chart([data])
                    //var idx = findChartIndex(data)
                    //chart_data.splice(idx, 1);
                    //console.log("unselect chart_data", idx, chart_data)
                    //trigger_chart_update(chart_data);
                }
            }
        } );  
        
        document.getElementById("btn-for-latency").style.display = "block";
        
        document.getElementById("id_perf_result").style.display = "block";
    }
    function delete_and_update_chart(data){
        console.log("delete_and_update_chart", data)
        for(var i = 0; i < data.length; i ++){
            var idx = findChartIndex(data[i].index)
            chart_data.splice(idx, 1);
            console.log("unselect chart_data", idx, chart_data)
        }
        trigger_chart_update(chart_data);
    }
    function query_result(group, table){
      console.debug("query_result",group)
      //keys = serializeResultFromInputList_li(li, 'gn-li-selected')
      $.ajax({
          'url': '/report/query_perf_result/',
          'type': 'POST',
          'data': {'keys':[group.test_key]},
          'success': function (data, textStatus, jqXHR) {
              console.debug("query_result return data",data.result)
              if (data.ok){
                gen_table(data.result, table)
              }
              else{
                alert(data.result);
              }
          },
          'error': function (jqXHR, textStatus, errorThrown) {
              alert("ajax error");
          }
      });
    }
    function createChild ( row ) {
        // This is the table we'll convert into a DataTable
        var key = row.data().test_key
        var table = $('<table class="display_childtable table-hover" width="100%"/>');
        
        // Display it the child row
        row.child( table ).show();
     
        // Initialise as a DataTable
        query_result(row.data(), table)
        //var usersTable = table.DataTable( {
            // ...
        //} );
    }
    
    function destroyChild(row) {
        var table = $("table", row.child());
        delete_and_update_chart(table.DataTable().rows(".selected").data())
        //table.detach();
        table.DataTable().destroy();
        
        // And then hide the row
        row.child.hide();
    }
    function gen_parent_table(table_data){
        console.debug('gen_parent_table: ',table_data)
        //if (table_data.length){
            var siteTable = $('#ParentTable').DataTable( {
                order: [ 1, 'asc' ],
                data: table_data,
                columns: [
                    {
                        className: 'details-control',
                        orderable: false,
                        data: null,
                        defaultContent: '',
                        width: '5%'
                    },
                    { data: 'name' },
                    { data: 'project_name'},
                    { data: 'tester'},
                    { data: 'start_time'},
                    { data: 'environment.ip'},      
                    {
                        data: null,
                        className: 'delete_col',
                        render: function (data, type, full, meta) {
                            //return '<a href="/case/'+ data.case_id + '/" target="_parent">' + escapeHTML(data.summary) + '</a>';
                            return '<a class="pficon pficon pficon-error-circle-o"></a>';
                        }
                    },
                ],
                select: {
                    toggleable: false
                },
                dom: "Brti",
                destroy: true,
            } );
            
            document.getElementById("id_perf_result").style.display = "block";
            //SeleteResultFromInputList(table_data)
        //}
    }
    
    function query_group(keys, isDelete){
        console.debug("query_group",keys)
        //var is_valid = 0;
        var new_url = '/report/performance/?confirm='+confirm;
        var new_keys = []
        for(var i in keys){
            console.debug("key:",i)
            var m = keys[i].search(/^\d+_[\w|\d]+/i)
            console.debug("match result:",m)
            if(m == 0){
                new_url += '&keys='+keys[i]
                is_valid = 1;
                new_keys.push(keys[i])
            }
        }
        if (isDelete == 1){
            ajax_url = '/report/delete_perf_group/';
            new_url = '/report/performance/?confirm='+confirm;
        }
        else{
            ajax_url = '/report/query_perf_group/';
        }
        console.debug("query_group ajax url", ajax_url)
        //var ref_url = window.location.href;
        //old_keys = ref_url.split('&keys=')
        //old_keys.shift()
        //old_keys.sort()
        //new_keys.sort()
        //console.debug('old_keys: ',old_keys)
        //console.debug('new_keys: ',new_keys)
        //if(new_keys.length > 50){
        //    alert("Load too much performance result, Please reduce!")
        //}
        //else{
        //    if(old_keys.toString() != new_keys.toString()){
        //        window.location.replace(new_url) 
        //        console.debug('url change!')  
        //    }
        //}
        if(new_keys.length > 50){
            alert("Load too much performance result, Please reduce!")
        }
        else{
            $.ajax({
                'url': ajax_url,
                'type': 'POST',
                'data': {'keys':new_keys},
                'success': function (data, textStatus, jqXHR) {
                    console.debug("query_group return data",data.result)
                    gen_parent_table(data.result)
                    chart_data = [];
                    trigger_chart_update([])
                    if (isDelete == 1){
                        window.location.replace(new_url) 
                    }
                    else{
                        history.pushState("", "Title", new_url);
                    }
                    //window.location.replace(new_url) 
                },
                'error': function (jqXHR, textStatus, errorThrown) {
                    alert("ajax error");
                }
            });
        }
    }
    function update_qos_table(data){
        if(data.length){
            var qos_table_data = gen_qos_data(data)
            console.debug("update_qos_table:", qos_table_data)
            if(qos_table_col != 0){
                var siteTable = $('#QosTable').DataTable()
                siteTable.destroy()
                $('#QosTable').empty()
            }
            var siteTable = $('#QosTable').DataTable( {
                order: [ 0, 'asc' ],
                columns:qos_table_data.title,
                data: qos_table_data.data,
                select: {
                    toggleable: false
                },
                dom: "t",
                destroy: true,
            } );  
            qos_table_col = data.length
            var chart = new CanvasJS.Chart("qos_chart", {
                theme: "light2",
                //animationEnabled: true,
                zoomEnabled: true,
                title: {
                    text: "SSD QOS"
                },
                toolTip: {
                    shared: true
                },
                axisX: {
                    valueFormatString: "####",
                    title: "Latency us",
                    //maximum: Math.max.apply(Math,qos_table_data.chart.map(item => { return item.x }))+100,
                    //minimum: Math.min.apply(Math,qos_table_data.chart.map(item => { return item.x }))-100
                },
                axisY:{
                        title: "Percentage",
                        labelFormatter: function ( e ) {
                            return Math.pow(10,e.value);  
                        }
                },
                legend: {
                    cursor: "pointer",
                    fontSize: 16,
                    itemclick: toggleDataSeries
                },    
                data: qos_table_data.chart
            });
            chart.render()
        }
        else{
            $('#QosTable').empty()
        }
    }
});

function gen_qos_data(data){
    var ret = {}
    var title = []
    var content = {}
    var chart_ret = []
    var clist = [
                    {'dis_name':'wr_avg','name':'avg_latency_write', 'data0':0, 'axisY':1},
                    {'dis_name':'wr_max','name':'max_latency_write', 'data0':0, 'axisY':0.000000001},
                    {'dis_name':'wr_99','name':'percent_99_write', 'data0':0, 'axisY':0.01},
                    {'dis_name':'wr_999','name':'percent_999_write', 'data0':0, 'axisY':0.001},
                    {'dis_name':'wr_9999','name':'percent_9999_write','data0':0, 'axisY':0.0001},
                    {'dis_name':'wr_99999','name':'percent_99999_write', 'data0':0, 'axisY':0.00001},
                    {'dis_name':'wr_999999','name':'percent_999999_write', 'data0':0, 'axisY':0.000001},
                    {'dis_name':'wr_9999999','name':'percent_9999999_write', 'data0':0, 'axisY':0.0000001},
                    {'dis_name':'wr_99999999','name':'percent_99999999_write', 'data0':0, 'axisY':0.00000001},
                    {'dis_name':'rd_avg','name':'avg_latency_read', 'data0':0, 'axisY':1},
                    {'dis_name':'rd_max','name':'max_latency_read', 'data0':0, 'axisY':0.000000001},
                    {'dis_name':'rd_99','name':'percent_99_read', 'data0':0, 'axisY':0.01},
                    {'dis_name':'rd_999','name':'percent_999_read', 'data0':0, 'axisY':0.001},
                    {'dis_name':'rd_9999','name':'percent_9999_read', 'data0':0, 'axisY':0.0001},
                    {'dis_name':'rd_99999','name':'percent_99999_read', 'data0':0, 'axisY':0.00001},
                    {'dis_name':'rd_999999','name':'percent_999999_read', 'data0':0, 'axisY':0.000001},
                    {'dis_name':'rd_9999999','name':'percent_9999999_read', 'data0':0, 'axisY':0.0000001},
                    {'dis_name':'rd_99999999','name':'percent_99999999_read', 'data0':0, 'axisY':0.00000001},
                ]
    title.push({ title: 'name', data: "dis_name" })
    //console.log("gen_qos_data:", data)
    console.log("log: ", Math.log(0.01))
    for (var i = 0;i < data.length; i++){
        console.log("gen_qos_data:", data[i])
        data_name = 'data'+i
        title.push({ title: data[i].group_name+'-'+data[i].name, data: data_name })
        for(var j = 0; j < clist.length; j++){
            clist[j][data_name] = data[i]['summary_report'][clist[j].name]
        }
        var element = {}
        var qos_data = gen_qos_data_point(data[i], clist);
        if(data[i]['summary_report']['max_latency_read'] != 0){
            element = {
                type: "line",
                name: data[i].group_name + ": " + data[i].name + "read",
                showInLegend: true,
                markerType: 'none',
                dataPoints: qos_data.read
            }
            chart_ret.push(element)
        }
        if(data[i]['summary_report']['max_latency_write'] != 0){
            element = {
                type: "line",
                name: data[i].group_name + ": " + data[i].name + "write",
                showInLegend: true,
                markerType: 'none',
                dataPoints: qos_data.write
            }
            chart_ret.push(element)
        }
    }
    console.debug("gen_qos_data:", title)
    console.debug("gen_qos_data:", clist)
    console.log("max: ", Math.max.apply(Math,qos_data.write.map(item => { return item.x })))
    console.log("min: ", Math.min.apply(Math,qos_data.read.map(item => { return item.x })))
    return {'title':title, 'data':clist, 'chart':chart_ret}

}

function gen_data_point(data, type){
    var ret = []
    console.log("gen_data_point", data.detail)
    for (var i = 0;i < data.detail.length; i++){
        var element = {};
        element.x = (data.detail[i].index)
        element.y = data.detail[i][type]
        ret.push(element)
    }
    console.log(ret)
    return ret;
}

function gen_qos_data_point(data, type, pat){
    var rd_ret = []
    var wr_ret = []
    console.log("gen_qos_data_point", data.detail)
    for (var i = 0;i < type.length; i++){
        var element = {};
        element.x = (data['summary_report'][type[i].name])
        element.y = Math.log10(type[i].axisY)
        if(/read/.test(type[i].name)){
            rd_ret.push(element)
        }
        else{
            wr_ret.push(element)
        }
    }
    wr_ret.sort(compareValues('y', 'desc'))
    rd_ret.sort(compareValues('y', 'desc'))
    return {'write':wr_ret, 'read':rd_ret};
}

function chart_data_update(src, dst){
    var update_ret = src;
    var is_find_id = 0
    console.log("chart_data_update before ", dst, src)
    console.log("chart_data_update before lenght ", dst.length, src.length)
    for(var j = 0; j < src.length; j++){
        is_find_id = 0;
        console.log("chart_data_update ID ", src[j].index, dst.result.index)
        if (src[j].index === dst.result.index){
            console.log("chart_data_update find ID ", update_ret)
            update_ret[j] = src.result;
            is_find_id = 1;
            break;
        }
    }
    if (is_find_id === 0){
        console.log("chart_data_update Not find ID ", update_ret)
        update_ret.push(dst.result)
    }
    console.log("chart_data_update after", update_ret)
    return update_ret
}


function serializeResultFromInputList_li(container, name) {
  var elements;
  var ids = [];
  elements = container.parent().find('li.'+name);
  
  elements.each(function(i) {
    console.log(this.title)
    ids.push(this.title);
  });

  return ids;
}

function serializeResultFromInputList_button(container, name) {
  var elements;
  var ids = [];
  elements = $('#'+container).find('button.'+name);
  
  elements.each(function(i) {
    console.log($(this).attr('data-column'))
    ids.push(parseInt($(this).attr('data-column')));
  });

  return ids;
}
function SeleteResultFromInputList(groups) {
  var elements;
  var ids = [];
  //console.debug(groups)

  //groups.forEach(function(val, index) {
  //  console.log(val, index);
  //});
  elements = $('.gn-menu').find('li.gn-li-unselected');
  elements.each(function(i) {
    for (var j = 0; j < groups.length; j++) {
        //console.debug(val)
        val = groups[j]
        //console.log(this.title, val.test_key)
        if(val.test_key == this.title){
            console.log(this.title)
            console.log("Find Group")
            console.debug(this)
            $(this).removeClass("gn-li-unselected")
            $(this).addClass("gn-li-selected")
        }
    }
  });

  //var li = $(".gn-icon-article").parent()
  //console.debug(data_type_list)
//
  //if (li.hasClass("gn-li-unselected")){
  //    li.removeClass("gn-li-unselected");
  //    li.addClass("gn-li-selected")
  //} else {
  //    li.removeClass("gn-li-selected");
  //    li.addClass("gn-li-unselected")
  //}
}
function displayLoadingDiv(){
    var loading_div = document.getElementById("loading_div");
    loading_div.style.display = 'block';
}

function hiddenLoadingDiv(){
    var loading_div = document.getElementById("loading_div");
    loading_div.style.display = 'none';
}

var whatleft = function(List1,List2){
    var bigList = [];
    var smallList = [];
    if(List1.length>=List2.length){//判断数组长度，决定最后输出的是哪一个数组
        bigList = List1;
        smallList = List2;
    }else{
        biglist = List2;
        smallList = List1;
    }
    for(let i = bigList.length-1;i>=0;i--){
        a = bigList[i];
        for(let j = smallList.length;j>=0;j--){
            b = smallList[j];
            if(a === b){
                bigList.splice(i,1); //从第i个元素开始（包括第i个元素），删除1个元素
                smallList.splice(j,1);
                break;
            }
        }
    }
    return bigList; 
}
function compareValues(key, order = 'asc') { 
  return function innerSort(a, b) { 
    if (!a.hasOwnProperty(key) || !b.hasOwnProperty(key)) { 
      // 该属性在其中一个对象上不存在 
      return 0; 
    } 
 
    const varA = (typeof a[key] === 'string') 
      ? a[key].toUpperCase() : a[key]; 
    const varB = (typeof b[key] === 'string') 
      ? b[key].toUpperCase() : b[key]; 
 
    let comparison = 0; 
    if (varA > varB) { 
      comparison = 1; 
    } else if (varA < varB) { 
      comparison = -1; 
    } 
    return ( 
      (order === 'desc') ? (comparison * -1) : comparison 
    ); 
  }; 
} 