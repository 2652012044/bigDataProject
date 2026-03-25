<template>
  <div class="keyword-trend-page">
    <div class="page-header">
      <h2 class="page-title">关键词趋势</h2>
      <p class="page-desc">小说领域热门关键词（标签）的热度排行与分析</p>
    </div>

    <el-alert v-if="notice" :title="notice" type="info" show-icon :closable="false" style="margin-bottom: 16px;" />

    <el-row :gutter="20">
      <el-col :span="17">
        <div class="card-box">
          <div class="card-header">
            <span class="card-title">关键词热度排行</span>
          </div>
          <div ref="trendChartRef" class="chart-container"></div>
        </div>
      </el-col>

      <el-col :span="7">
        <div class="card-box emerging-card">
          <div class="card-header">
            <span class="card-title">高热度关键词</span>
            <el-tag size="small" type="warning">按平均阅读量</el-tag>
          </div>
          <div class="emerging-list">
            <div v-for="(item, index) in emergingKeywords" :key="item.keyword" class="emerging-item">
              <div class="emerging-rank" :class="getRankClass(index)">{{ index + 1 }}</div>
              <div class="emerging-info">
                <el-tag size="small" effect="plain" class="emerging-tag">{{ item.keyword }}</el-tag>
              </div>
              <div class="emerging-trend">
                <span class="trend-value">{{ Number(item.avgReads).toLocaleString() }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import request from '@/api/index'

const trendChartRef = ref(null)
let trendChart = null
const topKeywords = ref([])
const emergingKeywords = ref([])
const notice = ref('')

const getRankClass = (index) => {
  if (index === 0) return 'rank-1'
  if (index === 1) return 'rank-2'
  if (index === 2) return 'rank-3'
  return ''
}

const colorPalette = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b8d0', '#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#9b59b6', '#1abc9c', '#e67e22', '#3f51b5', '#00bcd4', '#ff5722']

async function loadData() {
  try {
    const res = await request.get('/trend/keyword')
    const data = res.data || {}
    topKeywords.value = data.topKeywords || []
    emergingKeywords.value = data.emergingKeywords || []
    notice.value = data.notice || ''
    initChart()
  } catch (e) { /* keep empty */ }
}

function initChart() {
  if (!trendChartRef.value || topKeywords.value.length === 0) return
  trendChart = echarts.init(trendChartRef.value)

  const names = topKeywords.value.map(k => k.keyword)
  const counts = topKeywords.value.map(k => k.count)

  trendChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: params => `${params[0].name}：关联 ${params[0].value} 本书` },
    grid: { left: 100, right: 40, top: 10, bottom: 10 },
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'category', data: names.reverse(), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { fontSize: 13, color: '#606266' } },
    series: [{
      type: 'bar', barWidth: 16,
      data: counts.reverse().map((v, i) => ({
        value: v,
        itemStyle: { borderRadius: [0, 4, 4, 0], color: colorPalette[i % colorPalette.length] }
      })),
      label: { show: true, position: 'right', fontSize: 12, color: '#909399' }
    }]
  })
}

const handleResize = () => { trendChart?.resize() }
onMounted(() => { loadData(); window.addEventListener('resize', handleResize) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); trendChart?.dispose() })
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.keyword-trend-page { padding: $spacing-lg; background: $bg-page; min-height: calc(100vh - #{$top-nav-height}); }
.page-header { margin-bottom: $spacing-lg; .page-title { font-size: 22px; font-weight: 700; color: $text-primary; margin: 0 0 6px 0; } .page-desc { font-size: 13px; color: $text-secondary; margin: 0; } }
.card-box { background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-md; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: $spacing-md; .card-title { font-size: 16px; font-weight: 600; color: $text-primary; } }
.chart-container { width: 100%; height: 500px; }
.emerging-card {
  .emerging-list { display: flex; flex-direction: column; gap: 8px; }
  .emerging-item { display: flex; align-items: center; gap: 10px; padding: 9px 12px; border-radius: $border-radius-sm; background: $bg-color; cursor: pointer; transition: all 0.25s ease; &:hover { background: #edf0f5; transform: translateX(4px); } }
  .emerging-rank { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #fff; background: $info-color; flex-shrink: 0;
    &.rank-1 { background: linear-gradient(135deg, #f56c6c, #e6394a); } &.rank-2 { background: linear-gradient(135deg, #e6a23c, #d48806); } &.rank-3 { background: linear-gradient(135deg, #409eff, #3375b9); }
  }
  .emerging-info { flex: 1; .emerging-tag { font-size: 13px; } }
  .emerging-trend { display: flex; align-items: center; gap: 3px; flex-shrink: 0; font-size: 12px; font-weight: 600; color: $text-secondary; }
}
</style>
