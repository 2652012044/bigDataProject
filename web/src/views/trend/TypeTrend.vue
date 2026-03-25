<template>
  <div class="type-trend-page">
    <div class="page-header">
      <h2 class="page-title">类型趋势</h2>
      <p class="page-desc">小说各类型的书籍数量、阅读量与占比分析</p>
    </div>

    <el-alert v-if="notice" :title="notice" type="info" show-icon :closable="false" style="margin-bottom: 16px;" />

    <el-row :gutter="20">
      <el-col :span="17">
        <div class="card-box">
          <div class="card-header">
            <span class="card-title">类型书籍数量分布</span>
          </div>
          <div ref="mainChartRef" class="chart-container"></div>
        </div>
      </el-col>

      <el-col :span="7">
        <div class="card-box rise-fall-card">
          <div class="card-header">
            <span class="card-title">阅读量占比</span>
            <el-tag size="small" type="info">实时</el-tag>
          </div>
          <div class="rise-fall-list">
            <div v-for="(item, index) in riseFallList" :key="item.type" class="rise-fall-item">
              <div class="item-rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
              <div class="item-info">
                <span class="item-name">{{ item.type }}</span>
                <span class="item-count">{{ item.count }} 部</span>
              </div>
              <el-tag type="info" size="small" class="item-rate">{{ item.rate }}%</el-tag>
            </div>
          </div>
        </div>

        <div class="card-box summary-card">
          <div class="card-header"><span class="card-title">类型占比概览</span></div>
          <div ref="pieChartRef" class="pie-chart-container"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import request from '@/api/index'

const mainChartRef = ref(null)
const pieChartRef = ref(null)
let mainChart = null
let pieChart = null

const typeData = ref([])
const riseFallList = ref([])
const notice = ref('')

const typeColors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b8d0']

async function loadData() {
  try {
    const res = await request.get('/trend/type')
    const data = res.data || {}
    typeData.value = data.typeData || []
    riseFallList.value = data.riseFallList || []
    notice.value = data.notice || ''
    initCharts()
  } catch (e) { /* keep empty */ }
}

function initCharts() {
  if (mainChartRef.value && typeData.value.length > 0) {
    mainChart = echarts.init(mainChartRef.value)
    const names = typeData.value.map(t => t.type)
    const counts = typeData.value.map(t => t.count)

    mainChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 50, right: 30, top: 20, bottom: 35 },
      xAxis: { type: 'category', data: names, axisLabel: { color: '#606266', rotate: names.length > 8 ? 25 : 0 } },
      yAxis: { type: 'value', name: '书籍数量', nameTextStyle: { color: '#909399' }, splitLine: { lineStyle: { color: '#f0f2f5' } } },
      series: [{
        type: 'bar', barWidth: '50%',
        data: counts.map((v, i) => ({ value: v, itemStyle: { color: typeColors[i % typeColors.length], borderRadius: [4, 4, 0, 0] } })),
        label: { show: true, position: 'top', fontSize: 11, color: '#909399' }
      }]
    })
  }

  if (pieChartRef.value && typeData.value.length > 0) {
    pieChart = echarts.init(pieChartRef.value)
    pieChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} 部 ({d}%)' },
      series: [{
        type: 'pie', radius: ['40%', '70%'], center: ['50%', '52%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { fontSize: 12, color: '#606266' },
        data: typeData.value.map((t, i) => ({ name: t.type, value: t.count, itemStyle: { color: typeColors[i % typeColors.length] } }))
      }]
    })
  }
}

const handleResize = () => { mainChart?.resize(); pieChart?.resize() }

onMounted(() => { loadData(); window.addEventListener('resize', handleResize) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); mainChart?.dispose(); pieChart?.dispose() })
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.type-trend-page { padding: $spacing-lg; background: $bg-page; min-height: calc(100vh - #{$top-nav-height}); }
.page-header { margin-bottom: $spacing-lg; .page-title { font-size: 22px; font-weight: 700; color: $text-primary; margin: 0 0 6px 0; } .page-desc { font-size: 13px; color: $text-secondary; margin: 0; } }
.card-box { background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-md; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: $spacing-md; .card-title { font-size: 16px; font-weight: 600; color: $text-primary; } }
.chart-container { width: 100%; height: 420px; }
.pie-chart-container { width: 100%; height: 220px; }
.rise-fall-card {
  .rise-fall-list { display: flex; flex-direction: column; gap: 12px; }
  .rise-fall-item { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: $border-radius-sm; background: $bg-color; transition: all 0.25s ease; &:hover { background: #f7f8fb; transform: translateX(4px); } }
  .item-rank { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: #fff; background: $info-color; flex-shrink: 0;
    &.rank-1 { background: linear-gradient(135deg, #f56c6c, #e6394a); } &.rank-2 { background: linear-gradient(135deg, #e6a23c, #d48806); } &.rank-3 { background: linear-gradient(135deg, #409eff, #3375b9); }
  }
  .item-info { flex: 1; display: flex; flex-direction: column; gap: 2px; .item-name { font-size: 14px; font-weight: 600; color: $text-primary; } .item-count { font-size: 12px; color: $text-secondary; } }
  .item-rate { flex-shrink: 0; font-weight: 600; }
}
</style>
