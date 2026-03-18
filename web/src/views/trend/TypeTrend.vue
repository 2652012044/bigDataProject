<template>
  <div class="type-trend-page">
    <div class="page-header">
      <h2 class="page-title">类型趋势</h2>
      <p class="page-desc">小说各类型在不同月份的发展趋势与涨跌分析</p>
    </div>

    <el-row :gutter="20">
      <el-col :span="17">
        <div class="card-box">
          <div class="card-header">
            <span class="card-title">类型趋势变化（2025年）</span>
            <div class="card-actions">
              <el-radio-group v-model="chartMode" size="small">
                <el-radio-button value="stack">堆叠面积</el-radio-button>
                <el-radio-button value="line">折线</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div ref="mainChartRef" class="chart-container"></div>
        </div>
      </el-col>

      <el-col :span="7">
        <div class="card-box rise-fall-card">
          <div class="card-header">
            <span class="card-title">涨跌列表</span>
            <el-tag size="small" type="info">本月 vs 上月</el-tag>
          </div>
          <div class="rise-fall-list">
            <div
              v-for="(item, index) in riseFallList"
              :key="item.type"
              class="rise-fall-item"
            >
              <div class="item-rank" :class="'rank-' + (index + 1)">
                {{ index + 1 }}
              </div>
              <div class="item-info">
                <span class="item-name">{{ item.type }}</span>
                <span class="item-count">{{ item.count }} 部</span>
              </div>
              <el-tag
                :type="item.rate >= 0 ? 'success' : 'danger'"
                size="small"
                class="item-rate"
              >
                {{ item.rate >= 0 ? '+' : '' }}{{ item.rate }}%
              </el-tag>
            </div>
          </div>
        </div>

        <div class="card-box summary-card">
          <div class="card-header">
            <span class="card-title">类型占比概览</span>
          </div>
          <div ref="pieChartRef" class="pie-chart-container"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const mainChartRef = ref(null)
const pieChartRef = ref(null)
let mainChart = null
let pieChart = null
const chartMode = ref('stack')

const months = [
  '1月', '2月', '3月', '4月', '5月', '6月',
  '7月', '8月', '9月', '10月', '11月', '12月'
]

const typeData = {
  玄幻: [320, 332, 345, 360, 378, 390, 412, 425, 440, 458, 470, 490],
  都市: [220, 218, 230, 245, 258, 270, 282, 295, 310, 325, 338, 352],
  仙侠: [180, 175, 185, 192, 200, 215, 225, 238, 248, 260, 272, 285],
  科幻: [120, 128, 135, 148, 162, 175, 190, 205, 218, 235, 250, 268],
  言情: [260, 255, 268, 280, 295, 308, 318, 330, 342, 355, 365, 380]
}

const typeColors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']

const riseFallList = ref([
  { type: '科幻', count: 268, rate: 7.2 },
  { type: '玄幻', count: 490, rate: 4.3 },
  { type: '言情', count: 380, rate: 4.1 },
  { type: '仙侠', count: 285, rate: 3.8 },
  { type: '都市', count: 352, rate: 2.1 }
])

const buildMainOption = () => {
  const isStack = chartMode.value === 'stack'
  const types = Object.keys(typeData)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e4e7ed',
      textStyle: { color: '#303133' }
    },
    legend: {
      data: types,
      top: 10,
      textStyle: { color: '#606266' }
    },
    grid: {
      left: 50,
      right: 30,
      top: 55,
      bottom: 35
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: months,
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: { color: '#606266' }
    },
    yAxis: {
      type: 'value',
      name: '作品数量',
      nameTextStyle: { color: '#909399' },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f2f5' } },
      axisLabel: { color: '#606266' }
    },
    series: types.map((type, i) => ({
      name: type,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      stack: isStack ? 'total' : undefined,
      areaStyle: isStack
        ? { opacity: 0.35 }
        : undefined,
      emphasis: { focus: 'series' },
      lineStyle: { width: 2 },
      itemStyle: { color: typeColors[i] },
      data: typeData[type]
    }))
  }
}

const buildPieOption = () => {
  const types = Object.keys(typeData)
  const latestData = types.map((type, i) => ({
    name: type,
    value: typeData[type][11],
    itemStyle: { color: typeColors[i] }
  }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 部 ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '52%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          fontSize: 12,
          color: '#606266'
        },
        data: latestData
      }
    ]
  }
}

const initCharts = () => {
  if (mainChartRef.value) {
    mainChart = echarts.init(mainChartRef.value)
    mainChart.setOption(buildMainOption())
  }
  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
    pieChart.setOption(buildPieOption())
  }
}

const handleResize = () => {
  mainChart?.resize()
  pieChart?.resize()
}

watch(chartMode, () => {
  if (mainChart) {
    mainChart.setOption(buildMainOption(), true)
  }
})

onMounted(() => {
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  mainChart?.dispose()
  pieChart?.dispose()
  mainChart = null
  pieChart = null
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.type-trend-page {
  padding: $spacing-lg;
  background: $bg-page;
  min-height: calc(100vh - #{$top-nav-height});
}

.page-header {
  margin-bottom: $spacing-lg;

  .page-title {
    font-size: 22px;
    font-weight: 700;
    color: $text-primary;
    margin: 0 0 6px 0;
  }

  .page-desc {
    font-size: 13px;
    color: $text-secondary;
    margin: 0;
  }
}

.card-box {
  background: $bg-white;
  border-radius: $border-radius-md;
  box-shadow: $box-shadow-light;
  padding: $spacing-lg;
  margin-bottom: $spacing-md;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;

  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }
}

.chart-container {
  width: 100%;
  height: 420px;
}

.pie-chart-container {
  width: 100%;
  height: 220px;
}

.rise-fall-card {
  .rise-fall-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .rise-fall-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: $border-radius-sm;
    background: $bg-color;
    transition: all 0.25s ease;

    &:hover {
      background: #f7f8fb;
      transform: translateX(4px);
    }
  }

  .item-rank {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    color: #fff;
    background: $info-color;
    flex-shrink: 0;

    &.rank-1 {
      background: linear-gradient(135deg, #f56c6c, #e6394a);
    }

    &.rank-2 {
      background: linear-gradient(135deg, #e6a23c, #d48806);
    }

    &.rank-3 {
      background: linear-gradient(135deg, #409eff, #3375b9);
    }
  }

  .item-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;

    .item-name {
      font-size: 14px;
      font-weight: 600;
      color: $text-primary;
    }

    .item-count {
      font-size: 12px;
      color: $text-secondary;
    }
  }

  .item-rate {
    flex-shrink: 0;
    font-weight: 600;
  }
}

.summary-card {
  .pie-chart-container {
    margin-top: -8px;
  }
}
</style>
