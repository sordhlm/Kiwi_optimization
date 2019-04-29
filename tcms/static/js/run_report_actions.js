$(document).ready(function() {
    $('#export_report_to_pdf').click(function() {
        export_report_to_pdf();
    });

    $('.btnBlueCaserun').mouseover(function() {
      $(this).find('ul').show();
    }).mouseout(function() {
      $(this).find('ul').hide();
    });
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
    var option = {
      responsive: false,
      title: {
          display: true,
          text: 'Progress Rate Trend'
      }
    };

    canvas = document.getElementById("progress_trend");
    if(canvas){
        var labels = [];
        var line_com_data = [];
        var line_total_data = [];
        
        for(var i = 0;i < total_plan_count.length;i++){
            labels.push(total_plan_count[i].name)
            line_com_data.push(total_plan_count[i].TOTAL - total_plan_count[i].IDLE)
            line_total_data.push(total_plan_count[i].TOTAL)
        }
        var ctx = document.getElementById("progress_trend").getContext('2d');
        var myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Complete Test Cases Number",
                        //backgroundColor: 'rgb(255, 255, 255)',
                        borderColor: 'rgb(255, 99, 132)',
                        data: line_com_data
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
    option = {
      responsive: false,
      title: {
          display: true,
          text: 'Bugs Trend'
      }
    };
    canvas = document.getElementById("bug_trend");
    if(canvas){
        var ctx = document.getElementById("bug_trend").getContext('2d');
        var myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: bug_trend.date,
                datasets: [
                    {
                        label: "Open Bugs",
                        //backgroundColor: 'rgb(255, 255, 255)',
                        borderColor: 'rgb(255, 99, 132)',
                        lineTension: 0,
                        data: bug_trend.open
                    },
                    {
                        label: "Total Bugs",
                        //backgroundColor: 'rgb(255, 255, 255)',
                        borderColor: 'rgb(91,192,222)',
                        lineTension: 0,
                        data: bug_trend.total
                    },
                    {
                        label: "Closed Bugs",
                        //backgroundColor: 'rgb(255, 255, 255)',
                        borderColor: 'rgb(99, 192, 99)',
                        backgroundColor: 'rgb(239, 235, 163, 0.5)',
                        lineTension: 0,
                        fill: '-1',
                        data: bug_trend.close
                    }
                ]
            },
            options: option          
        });
    }    
    option = {
      responsive: false,
      cutoutPercentage: 50,
      title: {
          display: true,
          text: 'Complete Rate'
      }
    };

    canvas = document.getElementById("progress_rate");
    if(canvas){
        var pie_data = [];
        pie_data.push(total_plan_count[total_plan_count.length-1].PASSED)
        pie_data.push(total_plan_count[total_plan_count.length-1].FAILED)
        pie_data.push(total_plan_count[total_plan_count.length-1].BLOCKED)
        pie_data.push(total_plan_count[total_plan_count.length-1].IDLE)
        var data = {
            datasets: [{
                backgroundColor: ['rgb(92, 184, 92)','rgb(217,83,79)','rgb(240,173,78)','rgb(91,192,222)'],
                borderColor: ['rgb(92, 184, 92)','rgb(217,83,79)','rgb(240,173,78)','rgb(91,192,222)'],
                data: pie_data,
                hoverBorderWidth:10
            }],
        
            // These labels appear in the legend and in the tooltips when hovering different arcs
            labels: [
                'Passed',
                'Failed',
                'Blocked',
                'Idle'
            ]
        };
        var ctx = document.getElementById("progress_rate").getContext('2d');
        var myPieChart = new Chart(ctx,{
            type: 'pie',
            data: data,
            options: option
        });

    }
    option = {
      responsive: false,
      cutoutPercentage: 50,
      title: {
          display: true,
          text: 'Complete Rate'
      }
    };
    canvas = document.getElementById("feature_chart");
    if(canvas){
        var pie_data = [];
        pie_data.push(com_cnt.FAIL)
        pie_data.push(com_cnt.PASS)
        pie_data.push(com_cnt.RUNNING)
        pie_data.push(com_cnt.PENDING)
        var data = {
            datasets: [{
                backgroundColor: ['rgb(92, 184, 92)','rgb(217,83,79)','rgb(240,173,78)','rgb(91,192,222)'],
                borderColor: ['rgb(92, 184, 92)','rgb(217,83,79)','rgb(240,173,78)','rgb(91,192,222)'],
                data: pie_data,
                hoverBorderWidth:10
            }],
        
            // These labels appear in the legend and in the tooltips when hovering different arcs
            labels: [
                'PASS',
                'FAIL',
                'RUNNING',
                'PENDING'
            ]
        };
        var ctx = document.getElementById("feature_chart").getContext('2d');
        var myPieChart = new Chart(ctx,{
            type: 'pie',
            data: data,
            options: option
        });
    }
    //添加窗口尺寸改变响应监听
    //$(window).resize(resizeCanvas);
    //页面加载后先设置一下canvas大小
    //resizeCanvas();
});

 
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
