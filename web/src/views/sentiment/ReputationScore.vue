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
            <el-progress :percentage="row.positiveRate" :stroke-width="14" :color="getProgressColor(row.positiveRate)" :text-inside="true" />
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
      <h3 class="card-title">官方评分 vs 情感正面率 对比</h3>
      <div ref="barRef" class="chart-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import request from '@/api/index'

const barRef = ref(null)
let barChart = null
const rankingData = ref([])

const getProgressColor = (rate) => {
  if (rate >= 65) return '#67c23a'
  if (rate >= 50) return '#e6a23c'
  return '#f56c6c'
}

async function loadReputation() {
  try {
    const res = await request.get('/sentiment/reputation')
    rankingData.value = res.data || []
    initBarChart()
  } catch (e) { /* keep empty */ }
}

const initBarChart = () => {
  if (!barRef.value || rankingData.value.length === 0) return
  barChart = echarts.init(barRef.value)
  const top10 = rankingData.value.slice(0, 10)
  const names = top10.map(item => item.name)
  const officialScores = top10.map(item => item.officialScore)
  const positiveRates = top10.map(item => item.positiveRate)

  barChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['官方评分 (x10)', '情感正面率 (%)'], top: 4, textStyle: { fontSize: 13 } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: 50, containLabel: true },
    xAxis: { type: 'category', data: names, axisLabel: { fontSize: 12, color: '#606266', rotate: 20 } },
    yAxis: { type: 'value', axisLabel: { fontSize: 12, color: '#606266' }, max: 100 },
    color: ['#409eff', '#67c23a'],
    series: [
      {
        name: '官方评分 (x10)', type: 'bar', barWidth: 28, barGap: '20%',
        data: officialScores.map(s => (s * 10).toFixed(0)),
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top', fontSize: 11, color: '#409eff', formatter: params => officialScores[params.dataIndex] }
      },
      {
        name: '情感正面率 (%)', type: 'bar', barWidth: 28,
        data: positiveRates,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top', fontSize: 11, color: '#67c23a', formatter: '{c}%' }
      }
    ]
  })
}

const handleResize = () => { barChart?.resize() }

onMounted(() => {
  loadReputation()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  barChart?.dispose()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.reputation-score { padding: $spacing-lg; }
.page-title { font-size: 22px; font-weight: 600; color: $text-primary; margin-bottom: $spacing-lg; }
.card-box { background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-lg; }
.card-title { font-size: 16px; font-weight: 600; color: $text-primary; margin-bottom: $spacing-md; padding-left: $spacing-sm; border-left: 3px solid $primary-color; }
.chart-container { width: 100%; height: 420px; }
.rank-badge {
  display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center;
  border-radius: 50%; font-size: 14px; font-weight: 600; color: $text-regular; background: $bg-color;
  &.rank-top { color: #fff; background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); }
}
.score-text { font-size: 16px; font-weight: 700; color: $primary-color; }
.reputation-value { font-size: 16px; font-weight: 700; color: $warning-color; }
</style>
