<template>
  <div class="reputation-score">
    <h2 class="page-title">口碑评分</h2>

    <div class="card-box">
      <h3 class="card-title">口碑排行榜</h3>
      <el-table :data="rankingData" stripe style="width: 100%" :default-sort="{ prop: 'reputationIndex', order: 'descending' }">
        <el-table-column prop="rank" label="排名" width="80" align="center">
          <template #default="{ row }">
            <span :class="['rank-badge', { 'rank-top': row.rank <= 3 }]">{{ row.rank }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="小说名" min-width="140" />
        <el-table-column prop="officialScore" label="官方评分" min-width="110" align="center">
          <template #default="{ row }">
            <span class="score-text">{{ row.officialScore }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="positiveRate" label="情感正面率" min-width="130" align="center">
          <template #default="{ row }">
            <el-progress
              :percentage="row.positiveRate"
              :stroke-width="14"
              :color="getProgressColor(row.positiveRate)"
              :text-inside="true"
            />
          </template>
        </el-table-column>
        <el-table-column prop="reputationIndex" label="口碑指数" min-width="110" align="center" sortable>
          <template #default="{ row }">
            <span class="reputation-value">{{ row.reputationIndex }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="card-box">
      <h3 class="card-title">官方评分 vs 情感正面率 对比 (Top 10)</h3>
      <div ref="barRef" class="chart-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const barRef = ref(null)
let barChart = null

const rankingData = [
  { rank: 1, name: '诡秘之主', officialScore: 8.9, positiveRate: 71.5, reputationIndex: 92.3 },
  { rank: 2, name: '深海余烬', officialScore: 8.6, positiveRate: 68.9, reputationIndex: 88.7 },
  { rank: 3, name: '大奉打更人', officialScore: 8.3, positiveRate: 64.8, reputationIndex: 85.1 },
  { rank: 4, name: '斗破苍穹', officialScore: 8.1, positiveRate: 62.3, reputationIndex: 82.6 },
  { rank: 5, name: '道诡异仙', officialScore: 8.4, positiveRate: 60.2, reputationIndex: 80.4 },
  { rank: 6, name: '完美世界', officialScore: 7.9, positiveRate: 58.1, reputationIndex: 76.8 },
  { rank: 7, name: '遮天', officialScore: 7.7, positiveRate: 55.6, reputationIndex: 73.5 },
  { rank: 8, name: '凡人修仙传', officialScore: 7.5, positiveRate: 51.2, reputationIndex: 68.9 },
  { rank: 9, name: '夜的命名术', officialScore: 7.2, positiveRate: 47.3, reputationIndex: 62.4 },
  { rank: 10, name: '家族修仙', officialScore: 6.8, positiveRate: 42.1, reputationIndex: 55.7 }
]

const getProgressColor = (rate) => {
  if (rate >= 65) return '#67c23a'
  if (rate >= 50) return '#e6a23c'
  return '#f56c6c'
}

const initBarChart = () => {
  barChart = echarts.init(barRef.value)
  const names = rankingData.map((item) => item.name)
  const officialScores = rankingData.map((item) => item.officialScore)
  const positiveRates = rankingData.map((item) => item.positiveRate)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['官方评分 (x10)', '情感正面率 (%)'],
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
      data: names,
      axisLabel: {
        fontSize: 12,
        color: '#606266',
        rotate: 20
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 12, color: '#606266' },
      max: 100
    },
    color: ['#409eff', '#67c23a'],
    series: [
      {
        name: '官方评分 (x10)',
        type: 'bar',
        barWidth: 28,
        barGap: '20%',
        data: officialScores.map((s) => (s * 10).toFixed(0)),
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        label: {
          show: true,
          position: 'top',
          fontSize: 11,
          color: '#409eff',
          formatter: (params) => officialScores[params.dataIndex]
        }
      },
      {
        name: '情感正面率 (%)',
        type: 'bar',
        barWidth: 28,
        data: positiveRates,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        label: {
          show: true,
          position: 'top',
          fontSize: 11,
          color: '#67c23a',
          formatter: '{c}%'
        }
      }
    ]
  }
  barChart.setOption(option)
}

const handleResize = () => {
  barChart?.resize()
}

onMounted(() => {
  initBarChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  barChart?.dispose()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.reputation-score {
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

.chart-container {
  width: 100%;
  height: 420px;
}

.rank-badge {
  display: inline-block;
  width: 28px;
  height: 28px;
  line-height: 28px;
  text-align: center;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 600;
  color: $text-regular;
  background: $bg-color;

  &.rank-top {
    color: #fff;
    background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  }
}

.score-text {
  font-size: 16px;
  font-weight: 700;
  color: $primary-color;
}

.reputation-value {
  font-size: 16px;
  font-weight: 700;
  color: $warning-color;
}
</style>
