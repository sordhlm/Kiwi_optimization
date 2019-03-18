$(document).ready(function() {
    $('#export_report_to_pdf').click(function() {
        export_report_to_pdf();
    });
    var option = {
      responsive: false,
      title: {
          display: true,
          text: 'Progress Rate Trend'
      }
    };

    canvas = document.getElementById("myChart1");
    if(canvas){
        var labels = [];
        var line_com_data = [];
        var line_total_data = [];
        var pie_data = [];
        for(var i = 0;i < total_plan_count.length;i++){
            labels.push(total_plan_count[i].name)
            line_com_data.push(total_plan_count[i].TOTAL - total_plan_count[i].IDLE)
            line_total_data.push(total_plan_count[i].TOTAL)
        }
        var ctx = document.getElementById("myChart1").getContext('2d');
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
    canvas = document.getElementById("myChart3");
    if(canvas){
        var ctx = document.getElementById("myChart3").getContext('2d');
        var myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: bug_trend.date,
                datasets: [
                    {
                        label: "Total Bugs",
                        //backgroundColor: 'rgb(255, 255, 255)',
                        borderColor: 'rgb(255, 99, 132)',
                        lineTension: 0,
                        data: bug_trend.total
                    },
                    {
                        label: "Closed Bugs",
                        //backgroundColor: 'rgb(255, 255, 255)',
                        borderColor: 'rgb(91,192,222)',
                        lineTension: 0,
                        data: bug_trend.close
                    },
                    {
                        label: "Open Bugs",
                        //backgroundColor: 'rgb(255, 255, 255)',
                        borderColor: 'rgb(99, 192, 99)',
                        lineTension: 0,
                        data: bug_trend.open
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

    canvas = document.getElementById("myChart2");
    if(canvas){
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
        var ctx = document.getElementById("myChart2").getContext('2d');
        var myPieChart = new Chart(ctx,{
            type: 'pie',
            data: data,
            options: option
        });
    }

});

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
