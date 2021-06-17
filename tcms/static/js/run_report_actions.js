$(document).ready(function() {
    $('#export_report_to_pdf').click(function() {
        export_report_to_pdf();
    });

    $('.feature_name').mouseover(function() {
      console.debug("mouseover --")
      var component = jQ(this).attr('value')
      var genCaseTable = function(data) {
        console.debug(data)
        var table = $("#id_case_table").DataTable({
            data: data,
            columns: [
                { data: "case_id" },
                {
                    data: null,
                    render: function (data, type, full, meta) {
                        return '<a href="/case/'+ data.case_id + '/" target="_parent">' + escapeHTML(data.summary) + '</a>';
                    }
                },
                { data: "author" },
                { data: "create_date"},
            ],
            dom: "t",
            language: {
                zeroRecords: "No records found"
            },
            order: [[ 0, 'asc' ]],
            lengthMenu: [[50]],
            destroy: true,
        });
      }
      console.debug(component)
      jsonRPC('Component.filter_testcases', {product: product, component: component}, genCaseTable);
      document.getElementById("id_table_bg_container").style.display = 'block';
    }).mouseout(function() {
      console.debug("mouseout --")
      //document.getElementById("id_table_bg_container").style.display = 'none';
    });
    $("#id_table_bg_container").click(function(){
        document.getElementById("id_table_bg_container").style.display = 'none';
    })
    $('ul.statusOptions a').click(function() {
      var option = jQ(this).attr('value');
      console.debug(option)
      jQ(".com-status").each(function(index) {
        if ((jQ(this).is('.emphasize-' + option))||(option == 'ALL')) {
          jQ(this).parent().parent()[0].style.display = "table-row";
        } else {
          jQ(this).parent().parent()[0].style.display = "none";
        }
      });
    });
    gen_overview_chart();
    var option = {
      responsive: false,
      title: {
          display: true,
          text: 'Progress Rate Trend'
      }
    };
    canvas = document.getElementById("version_progress_trend");
    if(canvas){
        var labels = [];
        var line_pass_data = [];
        var line_fail_data = [];
        var line_total_data = [];
        console.debug(case_count_list)
        for(var i = 0;i < case_count_list.length;i++){
            labels.push(case_count_list[i].date)
            //line_com_data.push(case_count_list[i].TOTAL - case_count_list[i].IDLE)
            line_fail_data.push(case_count_list[i].FAILED)
            line_pass_data.push(case_count_list[i].PASSED)
            line_total_data.push(case_count_list[i].TOTAL)
        }
        var ctx = document.getElementById("version_progress_trend").getContext('2d');
        var myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Failed Test Cases Number",
                        //backgroundColor: 'rgb(255, 255, 255)',
                        borderColor: 'rgb(255, 99, 132)',
                        data: line_fail_data
                    },
                    {
                        label: "Passed Test Cases Number",
                        //backgroundColor: 'rgb(255, 255, 255)',
                        borderColor: 'rgb(92, 184, 92)',
                        data: line_pass_data
                    },
                    {
                        label: "Total Test Cases Number",
                        //backgroundColor: 'rgb(255, 255, 255)',
                        borderColor: 'rgb(99, 99, 132)',
                        data: line_total_data
                    }
                ]
            },
            options: option          
        });

    }
    canvas = document.getElementById("version_progress_trend_container");
    if(canvas){
        console.debug(case_count_list)
        if(case_count_list.length !== 0){
            document.getElementById("progress_container").style.display = 'block';
            gen_progress_trend(case_count_list, "version_progress_trend_container");
        }
        else{
            document.getElementById("progress_container").style.display = 'none';
        }
    }
    canvas = document.getElementById("feature_chart");
    if(canvas){
        var pie_data = [];
        pie_data.push(com_cnt.FAIL)
        pie_data.push(com_cnt.PASS)
        pie_data.push(com_cnt.RUNNING)
        pie_data.push(com_cnt.PENDING)
        var color = ['rgb(92, 184, 92)','rgb(217,83,79)','rgb(240,173,78)','rgb(91,192,222)']
        var labels = ['PASS','FAIL','RUNNING','PENDING']
        gen_pie_chart(pie_data,"feature_chart", color, labels)
    }
    $('#id_bug_step').change(function() {
        step = $(this).val();
        if (step) {
            console.debug(step)
            update_bug_trend(product, step)
        }
    });
    $('#id_progress_step').change(function() {
        step = $(this).val();
        is_run_base = $("#id_type").val()
        if (step) {
            console.debug(step)
            update_progress_trend(product, is_run_base, step)
        }
    });
    $('#id_type').change(function() {
        step = $("#id_progress_step").val();
        is_run_base = $(this).val()
        console.debug(is_run_base)
        if (is_run_base) {
            console.debug(step)
            update_progress_trend(product, is_run_base, step)
        }
    });
    $('#id_version_progress_step').change(function() {
        step = $(this).val();
        is_run_base = $("#id_version_type").val()
        console.debug(version)
        console.debug(is_run_base)
        if (step) {
            console.debug(step)
            update_version_progress_trend(product, version, is_run_base, step)
        }
    });
    $('#id_version_type').change(function() {
        step = $("#id_version_progress_step").val();
        is_run_base = $(this).val()
        console.debug(is_run_base)
        if (is_run_base) {
            console.debug(step)
            update_version_progress_trend(product, version, is_run_base, step)
        }
    });
});

function update_progress_trend(product_id, is_run_base, step){
  //console.debug(product_id)
  displayLoadingDiv();
  jQ.ajax({
    'url': '/report/update_progress_trend/',
    'type': 'POST',
    'data': {'product_id': product_id, 'is_run_base':is_run_base, 'step': step },
    'success': function (data, textStatus, jqXHR) {
      console.debug(data.result)
      gen_progress_trend(data.result, "chartContainer");
      gen_progress_pie(data.result, "progress_rate");
      hiddenLoadingDiv();
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    }
  });
}

function update_version_progress_trend(product_id, version_id, is_run_base, step){
  //console.debug(product_id)
  //displayLoadingDiv();
  jQ.ajax({
    'url': '/report/update_progress_trend/',
    'type': 'POST',
    'data': {'product_id': product_id, 'version_id':version_id, 'is_run_base':is_run_base, 'step': step },
    'success': function (data, textStatus, jqXHR) {
      console.debug(data.result)
      if(data.result.length !== 0){
        document.getElementById("progress_container").style.display = 'block';
        gen_progress_trend(data.result, "version_progress_trend_container");
      }
      else{
        document.getElementById("progress_container").style.display = 'none';
      }
      //hiddenLoadingDiv();
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    }
  });
}

function gen_overview_chart(){
    id_type = document.getElementById("id_type");
    if(id_type){
        $("#id_type").val(0)
    }
    id_progress_step = document.getElementById("id_progress_step");
    if(id_progress_step){
        $("#id_progress_step").val(1)
    }
    id_bug_step = document.getElementById("id_bug_step");
    if(id_bug_step){
        $("#id_bug_step").val(7)
    }
    canvas = document.getElementById("bug_trend");
    if(canvas){
        gen_bug_trend(bug_trend, "bug_trend");
    }      

    canvas = document.getElementById("progress_rate");
    if(canvas){
        gen_progress_pie(total_plan_count, "progress_rate");
        //var pie_data = [];
        //pie_data.push(total_plan_count[total_plan_count.length-1].PASSED)
        //pie_data.push(total_plan_count[total_plan_count.length-1].FAILED)
        //pie_data.push(total_plan_count[total_plan_count.length-1].BLOCKED)
        //pie_data.push(total_plan_count[total_plan_count.length-1].RUNNING)
        //pie_data.push(total_plan_count[total_plan_count.length-1].TOTAL - 
        //              total_plan_count[total_plan_count.length-1].PASSED - 
        //              total_plan_count[total_plan_count.length-1].FAILED -
        //              total_plan_count[total_plan_count.length-1].RUNNING - 
        //              total_plan_count[total_plan_count.length-1].BLOCKED);
        //color = ['rgb(92, 184, 92)','rgb(217,83,79)','rgb(240,173,78)','rgb(91,192,222)','rgb(191,191,191)'];
        //labels = ['Passed','Failed','Blocked','Running','Idle'];
        //gen_pie_chart(pie_data,"progress_rate", color, labels);
    }
    canvas = document.getElementById("chartContainer");
    if(canvas){
       gen_progress_trend(total_plan_count,"chartContainer");
    }
}
function update_bug_trend(product_id, step){
  //console.debug(product_id)
  displayLoadingDiv();
  jQ.ajax({
    'url': '/report/update_bug_trend/',
    'type': 'POST',
    'data': {'product_id': product_id, 'step': step },
    'success': function (data, textStatus, jqXHR) {
      //console.debug(data.result)
      gen_bug_trend(data.result, "bug_trend");
      hiddenLoadingDiv();
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    }
  });
}

function gen_progress_pie(data, container){
    var pie_data = [];
    pie_data.push(data[data.length-1].PASSED)
    pie_data.push(data[data.length-1].FAILED)
    pie_data.push(data[data.length-1].BLOCKED)
    pie_data.push(data[data.length-1].RUNNING)
    pie_data.push(data[data.length-1].TOTAL - 
                  data[data.length-1].PASSED - 
                  data[data.length-1].FAILED -
                  data[data.length-1].RUNNING - 
                  data[data.length-1].BLOCKED);
    color = ['rgb(92, 184, 92)','rgb(217,83,79)','rgb(240,173,78)','rgb(91,192,222)','rgb(191,191,191)'];
    labels = ['Passed','Failed','Blocked','Running','Idle'];
    gen_pie_chart(pie_data, container, color, labels);    
}
function gen_bug_trend(data, container){
    var option = {
      responsive: false,
      title: {
          display: true,
          text: 'Bugs Trend'
      }
    };
    var ctx = document.getElementById(container).getContext('2d');
    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.date,
            datasets: [
                {
                    label: "Open Bugs",
                    //backgroundColor: 'rgb(255, 255, 255)',
                    borderColor: 'rgb(255, 99, 132)',
                    lineTension: 0,
                    data: data.open
                },
                {
                    label: "Total Bugs",
                    //backgroundColor: 'rgb(255, 255, 255)',
                    borderColor: 'rgb(91,192,222)',
                    lineTension: 0,
                    data: data.total
                },
                {
                    label: "Closed Bugs",
                    //backgroundColor: 'rgb(255, 255, 255)',
                    borderColor: 'rgb(99, 192, 99)',
                    backgroundColor: 'rgb(239, 235, 163, 0.5)',
                    lineTension: 0,
                    fill: '-1',
                    data: data.close
                }
            ]
        },
        options: option          
    });
}
function gen_pie_chart(data, container, color, labels){
    var option = {
      responsive: false,
      cutoutPercentage: 50,
      title: {
          display: true,
          text: 'Complete Rate'
      }
    };
    var pie_data = {
        datasets: [{
            backgroundColor: color,
            borderColor: color,
            data: data,
            hoverBorderWidth:10
        }],
    
        // These labels appear in the legend and in the tooltips when hovering different arcs
        labels: labels
    };
    var ctx = document.getElementById(container).getContext('2d');
    var myPieChart = new Chart(ctx,{
        type: 'pie',
        data: pie_data,
        options: option
    });    
}
function gen_progress_trend(data, container){
    var pass_data = [];
    var fail_data = [];
    var idle_data = [];
    var running_data = [];
    //console.debug(case_count_list)
    for(var i = 0;i < data.length;i++){
        date = new Date(data[i].date)
        element = {};
        element.x = date;
        element.y = data[i].FAILED;
        fail_data.push(element);
        element = {};
        element.x = date;
        element.y = data[i].PASSED;
        pass_data.push(element);
        element = {};
        element.x = date;
        element.y = data[i].RUNNING;
        running_data.push(element);
        element = {};
        element.x = date;
        element.y = data[i].TOTAL - data[i].PASSED - data[i].FAILED - data[i].RUNNING;
        idle_data.push(element);            
    }
    console.debug("fail:", fail_data)
    //console.debug(pass_data)
    //console.debug(running_data)
    var chart = new CanvasJS.Chart(container, {
        animationEnabled: true,
        zoomEnabled: true,
        title:{
            text: "Progress Trend",
            fontFamily: "arial black",
            fontColor: "#695A42"
        },
        //axisX: {
        //    interval: 1,
        //    intervalType: "Day"
        //},
        axisY:{
            suffix: "%"
        },
        toolTip: {
            shared: true,
            content: toolTipContent
        },
        data: [
            {
                type: "stackedColumn100",
                showInLegend: true,
                color: "rgb(255, 99, 132)",
                name: "Failed",
                indexLabel: "#percent %",
                indexLabelPlacement: "inside",
                indexLabelFontColor: "white",
                dataPoints: fail_data
            },
            {        
                type: "stackedColumn100",
                showInLegend: true,
                name: "Passed",
                indexLabel: "#percent %",
                indexLabelPlacement: "inside",
                indexLabelFontColor: "white",
                color: "rgb(92, 184, 92)",
                dataPoints: pass_data
            },
            {        
                type: "stackedColumn100",
                showInLegend: true,
                name: "Running",
                //indexLabel: "#percent %",
                //indexLabelPlacement: "inside",
                //indexLabelFontColor: "white",
                color: "rgb(91,192,222)",
                dataPoints: running_data
            },
            {        
                type: "stackedColumn100",
                showInLegend: false,
                fillOpacity: 0.3,
                name: "Idle",
                color: "rgb(191,191,191)",
                dataPoints: idle_data
            }
            ]
    });
    chart.render();
    
    function toolTipContent(e) {
        var str = "";
        var total = 0;
        var str2, str3;
        for (var i = 0; i < e.entries.length; i++){
            var  str1 = "<span style= \"color:"+e.entries[i].dataSeries.color + "\"> "+e.entries[i].dataSeries.name+"</span>: <strong>"+e.entries[i].dataPoint.y+"</strong><br/>";
            total = e.entries[i].dataPoint.y + total;
            str = str.concat(str1);
        }
        date = (e.entries[0].dataPoint.x).getMonth()+'-'+(e.entries[0].dataPoint.x).getDate()
        str2 = "<span style = \"color:DodgerBlue;\"><strong>"+date+"</strong></span><br/>";
        total = Math.round(total * 100) / 100;
        str3 = "<span style = \"color:Tomato\">Total:</span><strong> "+total+"</strong><br/>";
        return (str2.concat(str)).concat(str3);
    }
}

//窗口尺寸改变响应（修改canvas大小）
function resizeCanvas() {
    $("#myChart3").attr("width", $(window).get(0).innerWidth);
    $("#myChart3").attr("height", $(window).get(0).innerHeight/2);
};
function export_report_to_pdf(){
    var title = (jQ('.report_sub_title')[0].textContent);
    var run_id = parseInt(title.match(/[\d+]/)[0]);
    var spin = jQ('.export').find("div").first();
    var text = jQ('.export').find('strong').first();
    text.fadeIn("fast");
    spin.addClass('spinner spinner-xs spinner-inline');
 
    jQ.ajax({
        'url': '/run/export_run_report_pdf/',
        'type': 'GET',
        'data': {'id': run_id},
        'success': function () {
            text.fadeOut("fast");
            spin.removeClass('spinner spinner-xs spinner-inline');
        },
        'error': function(){
            alert("gen fail")
        }
    });    
}

function displayLoadingDiv(){
    var loading_div = document.getElementById("loading_div");
    loading_div.style.display = 'block';
}

function hiddenLoadingDiv(){
    var loading_div = document.getElementById("loading_div");
    //console.debug("hidden loading");
    loading_div.style.display = 'none';
}