<template>
  <div class="sentiment-classify">
    <h2 class="page-title">情感分类</h2>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="10">
        <div class="card-box">
          <h3 class="card-title">情感分布</h3>
          <div ref="doughnutRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :span="14">
        <div class="card-box">
          <h3 class="card-title">情感趋势 (2025)</h3>
          <div ref="lineRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <div class="card-box table-card">
      <h3 class="card-title">近期情感分析结果</h3>
      <el-table :data="tableData" stripe style="width: 100%">
        <el-table-column prop="name" label="小说名" min-width="140" />
        <el-table-column prop="commentCount" label="评论数" min-width="100" align="center" />
        <el-table-column prop="positiveRate" label="正面占比" min-width="110" align="center">
          <template #default="{ row }">
            <span class="rate-positive">{{ row.positiveRate }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="negativeRate" label="负面占比" min-width="110" align="center">
          <template #default="{ row }">
            <span class="rate-negative">{{ row.negativeRate }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="overall" label="综合评价" min-width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getTagType(row.overall)" effect="light">{{ row.overall }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const doughnutRef = ref(null)
const lineRef = ref(null)
let doughnutChart = null
let lineChart = null

const tableData = [
  { name: '斗破苍穹', commentCount: 18620, positiveRate: '62.3%', negativeRate: '15.7%', overall: '好评' },
  { name: '完美世界', commentCount: 15340, positiveRate: '58.1%', negativeRate: '18.4%', overall: '好评' },
  { name: '遮天', commentCount: 13870, positiveRate: '55.6%', negativeRate: '20.2%', overall: '好评' },
  { name: '凡人修仙传', commentCount: 12450, positiveRate: '51.2%', negativeRate: '22.8%', overall: '中评' },
  { name: '诡秘之主', commentCount: 21030, positiveRate: '71.5%', negativeRate: '8.3%', overall: '好评' },
  { name: '大奉打更人', commentCount: 16780, positiveRate: '64.8%', negativeRate: '12.1%', overall: '好评' },
  { name: '夜的命名术', commentCount: 9870, positiveRate: '47.3%', negativeRate: '26.5%', overall: '中评' },
  { name: '深海余烬', commentCount: 11250, positiveRate: '68.9%', negativeRate: '10.7%', overall: '好评' },
  { name: '道诡异仙', commentCount: 14560, positiveRate: '60.2%', negativeRate: '17.3%', overall: '好评' },
  { name: '家族修仙', commentCount: 8340, positiveRate: '42.1%', negativeRate: '30.4%', overall: '差评' }
]

const getTagType = (overall) => {
  if (overall === '好评') return 'success'
  if (overall === '中评') return 'warning'
  return 'danger'
}

const initDoughnutChart = () => {
  doughnutChart = echarts.init(doughnutRef.value)
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}% ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: '8%',
      top: 'center',
      itemWidth: 14,
      itemHeight: 14,
      textStyle: { fontSize: 14, color: '#606266' }
    },
    color: ['#67c23a', '#909399', '#f56c6c'],
    series: [
      {
        name: '情感分布',
        type: 'pie',
        radius: ['45%', '72%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 3
        },
        label: {
          show: true,
          fontSize: 13,
          formatter: '{b}\n{d}%'
        },
        emphasis: {
          label: { show: true, fontSize: 16, fontWeight: 'bold' },
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.2)' }
        },
        data: [
          { value: 45, name: '正面' },
          { value: 30, name: '中性' },
          { value: 25, name: '负面' }
        ]
      }
    ]
  }
  doughnutChart.setOption(option)
}

const initLineChart = () => {
  lineChart = echarts.init(lineRef.value)
  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['正面', '中性', '负面'],
      top: 4,
      textStyle: { fontSize: 13 }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 50,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: months,
      axisLabel: { fontSize: 12, color: '#606266' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 12, color: '#606266', formatter: '{value}%' },
      max: 70
    },
    color: ['#67c23a', '#909399', '#f56c6c'],
    series: [
      {
        name: '正面',
        type: 'line',
        smooth: true,
        data: [42, 44, 43, 46, 48, 47, 50, 49, 51, 48, 46, 45],
        areaStyle: { opacity: 0.08 }
      },
      {
        name: '中性',
        type: 'line',
        smooth: true,
        data: [32, 30, 31, 29, 28, 30, 27, 28, 26, 29, 30, 30],
        areaStyle: { opacity: 0.08 }
      },
      {
        name: '负面',
        type: 'line',
        smooth: true,
        data: [26, 26, 26, 25, 24, 23, 23, 23, 23, 23, 24, 25],
        areaStyle: { opacity: 0.08 }
      }
    ]
  }
  lineChart.setOption(option)
}

const handleResize = () => {
  doughnutChart?.resize()
  lineChart?.resize()
}

onMounted(() => {
  initDoughnutChart()
  initLineChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  doughnutChart?.dispose()
  lineChart?.dispose()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.sentiment-classify {
  padding: $spacing-lg;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: $spacing-lg;
}

.card-box {
  background: $bg-white;
  border-radius: $border-radius-md;
  box-shadow: $box-shadow-light;
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: $spacing-md;
  padding-left: $spacing-sm;
  border-left: 3px solid $primary-color;
}

.chart-row {
  margin-bottom: 0;
}

.chart-container {
  width: 100%;
  height: 360px;
}

.table-card {
  .rate-positive {
    color: $success-color;
    font-weight: 600;
  }

  .rate-negative {
    color: $danger-color;
    font-weight: 600;
  }
}
</style>
