<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">类型统计</h2>
      <p class="page-desc">小说类型分布与年度趋势统计分析</p>
    </div>

    <!-- 顶部：堆叠柱状图 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="card-box">
          <div class="card-box-header">
            <span class="card-box-title">各类型小说年度趋势 (2020-2025)</span>
            <div class="chart-actions">
              <el-radio-group v-model="chartMode" size="small">
                <el-radio-button value="stacked">堆叠</el-radio-button>
                <el-radio-button value="grouped">分组</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div ref="barChartRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 底部：矩形树图 + 汇总卡片 -->
    <el-row :gutter="20">
      <el-col :span="16">
        <div class="card-box">
          <div class="card-box-header">
            <span class="card-box-title">当前类型分布 (矩形树图)</span>
          </div>
          <div ref="treemapRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="card-box summary-box">
          <div class="card-box-header">
            <span class="card-box-title">类型数据汇总</span>
          </div>
          <div class="summary-list">
            <div
              v-for="(item, index) in typesSummary"
              :key="item.name"
              class="summary-item"
            >
              <div class="summary-rank" :style="{ background: typeColors[index] }">
                {{ index + 1 }}
              </div>
              <div class="summary-info">
                <div class="summary-name">{{ item.name }}</div>
                <el-progress
                  :percentage="item.percent"
                  :color="typeColors[index]"
                  :stroke-width="8"
                  :show-text="false"
                />
              </div>
              <div class="summary-values">
                <span class="summary-count">{{ item.total.toLocaleString() }}部</span>
                <span class="summary-percent">{{ item.percent }}%</span>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

// ==================== Mock Data ====================
const years = ['2020', '2021', '2022', '2023', '2024', '2025']
const typeNames = ['玄幻', '都市', '仙侠', '科幻', '言情', '历史', '悬疑']
const typeColors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#9b59b6', '#1abc9c', '#e67e22']

const typeData = {
  '玄幻': [1200, 1350, 1580, 1720, 1890, 2050],
  '都市': [980, 1100, 1250, 1380, 1460, 1520],
  '仙侠': [850, 920, 1050, 1180, 1300, 1420],
  '科幻': [620, 750, 890, 1050, 1230, 1380],
  '言情': [780, 850, 920, 980, 1030, 1060],
  '历史': [540, 580, 620, 650, 680, 710],
  '悬疑': [420, 480, 560, 650, 740, 830]
}

const typesSummary = ref(
  typeNames.map((name, index) => {
    const values = typeData[name]
    const total = values[values.length - 1]
    return { name, total, percent: 0, color: typeColors[index] }
  }).sort((a, b) => b.total - a.total)
)

// Calculate percentages
const grandTotal = typesSummary.value.reduce((sum, item) => sum + item.total, 0)
typesSummary.value.forEach(item => {
  item.percent = parseFloat(((item.total / grandTotal) * 100).toFixed(1))
})

// ==================== State ====================
const barChartRef = ref(null)
const treemapRef = ref(null)
let barChart = null
let treemapChart = null
const chartMode = ref('stacked')

// ==================== Methods ====================
function initBarChart() {
  if (!barChartRef.value) return
  barChart = echarts.init(barChartRef.value)
  updateBarChart()
}

function updateBarChart() {
  if (!barChart) return

  const isStacked = chartMode.value === 'stacked'

  const series = typeNames.map((name, index) => ({
    name,
    type: 'bar',
    stack: isStacked ? 'total' : undefined,
    barWidth: isStacked ? '40%' : undefined,
    barGap: isStacked ? undefined : '10%',
    emphasis: {
      focus: 'series'
    },
    itemStyle: {
      color: typeColors[index],
      borderRadius: isStacked ? (index === typeNames.length - 1 ? [4, 4, 0, 0] : 0) : [4, 4, 0, 0]
    },
    data: typeData[name]
  }))

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        let html = `<div style="font-weight:bold;margin-bottom:6px;">${params[0].axisValue}年</div>`
        let total = 0
        params.forEach(p => {
          total += p.value
          html += `<div style="display:flex;align-items:center;justify-content:space-between;min-width:180px;">
            <span>${p.marker} ${p.seriesName}</span>
            <span style="font-weight:bold;margin-left:16px;">${p.value.toLocaleString()}</span>
          </div>`
        })
        html += `<div style="border-top:1px solid #eee;margin-top:6px;padding-top:6px;display:flex;justify-content:space-between;">
          <span>合计</span><span style="font-weight:bold;">${total.toLocaleString()}</span>
        </div>`
        return html
      }
    },
    legend: {
      data: typeNames,
      top: 0,
      textStyle: { fontSize: 13 }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '40px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: years,
      axisLabel: {
        fontSize: 13,
        formatter: '{value}年'
      },
      axisTick: { alignWithLabel: true }
    },
    yAxis: {
      type: 'value',
      name: '小说数量 (部)',
      nameTextStyle: {
        fontSize: 12,
        color: '#909399'
      },
      axisLabel: { fontSize: 12 },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#e4e7ed' }
      }
    },
    series,
    animationDuration: 1000,
    animationEasing: 'cubicOut'
  }

  barChart.setOption(option, true)
}

function initTreemap() {
  if (!treemapRef.value) return
  treemapChart = echarts.init(treemapRef.value)

  const treemapData = typeNames.map((name, index) => {
    const latestValue = typeData[name][typeData[name].length - 1]
    return {
      name,
      value: latestValue,
      itemStyle: {
        color: typeColors[index],
        borderColor: '#fff',
        borderWidth: 2
      }
    }
  })

  const option = {
    tooltip: {
      formatter: (params) => {
        const percent = ((params.value / grandTotal) * 100).toFixed(1)
        return `
          <div style="font-weight:bold;margin-bottom:4px;">${params.name}</div>
          <div>小说数量: ${params.value.toLocaleString()} 部</div>
          <div>占比: ${percent}%</div>
        `
      }
    },
    series: [{
      type: 'treemap',
      width: '95%',
      height: '90%',
      top: '5%',
      left: '2.5%',
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      label: {
        show: true,
        formatter: (params) => {
          const percent = ((params.value / grandTotal) * 100).toFixed(1)
          return `{name|${params.name}}\n{value|${params.value.toLocaleString()}部}\n{percent|${percent}%}`
        },
        rich: {
          name: {
            fontSize: 16,
            fontWeight: 'bold',
            color: '#fff',
            lineHeight: 28
          },
          value: {
            fontSize: 13,
            color: 'rgba(255,255,255,0.9)',
            lineHeight: 22
          },
          percent: {
            fontSize: 20,
            fontWeight: 'bold',
            color: '#fff',
            lineHeight: 28
          }
        },
        align: 'center',
        verticalAlign: 'middle'
      },
      itemStyle: {
        borderRadius: 6,
        gapWidth: 3
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 15,
          shadowColor: 'rgba(0, 0, 0, 0.3)'
        }
      },
      levels: [{
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 3,
          gapWidth: 3
        }
      }],
      data: treemapData,
      animationDuration: 1200,
      animationEasing: 'cubicOut'
    }]
  }

  treemapChart.setOption(option)
}

function handleResize() {
  barChart && barChart.resize()
  treemapChart && treemapChart.resize()
}

// ==================== Watchers ====================
watch(chartMode, () => {
  updateBarChart()
})

// ==================== Lifecycle ====================
onMounted(() => {
  initBarChart()
  initTreemap()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (barChart) {
    barChart.dispose()
    barChart = null
  }
  if (treemapChart) {
    treemapChart.dispose()
    treemapChart = null
  }
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.page-container {
  padding: $spacing-lg;
  min-height: 100%;
}

.page-header {
  margin-bottom: $spacing-lg;

  .page-title {
    font-size: 22px;
    font-weight: 600;
    color: $text-primary;
    margin: 0 0 $spacing-xs 0;
  }

  .page-desc {
    font-size: 14px;
    color: $text-secondary;
    margin: 0;
  }
}

.card-box {
  background: $bg-white;
  border-radius: $border-radius-md;
  box-shadow: $box-shadow-light;
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;

  .card-box-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-md;

    .card-box-title {
      font-size: 16px;
      font-weight: 600;
      color: $text-primary;
    }
  }
}

.chart-container {
  width: 100%;
  height: 420px;
}

.chart-actions {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.summary-box {
  .summary-list {
    display: flex;
    flex-direction: column;
    gap: $spacing-md;
  }

  .summary-item {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: $spacing-sm 0;

    .summary-rank {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 13px;
      font-weight: 600;
      flex-shrink: 0;
    }

    .summary-info {
      flex: 1;
      min-width: 0;

      .summary-name {
        font-size: 14px;
        font-weight: 500;
        color: $text-primary;
        margin-bottom: $spacing-xs;
      }
    }

    .summary-values {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      flex-shrink: 0;

      .summary-count {
        font-size: 14px;
        font-weight: 600;
        color: $text-primary;
      }

      .summary-percent {
        font-size: 12px;
        color: $text-secondary;
        margin-top: 2px;
      }
    }
  }
}
</style>
