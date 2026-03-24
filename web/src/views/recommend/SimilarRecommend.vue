<template>
  <div class="similar-recommend-page">
    <div class="page-header">
      <h2 class="page-title">相似推荐</h2>
      <p class="page-desc">选择一本小说，发现与之相似的作品关系网络</p>
    </div>

    <div class="search-bar">
      <el-select v-model="selectedNovelId" filterable placeholder="搜索或选择一本小说" size="large" class="novel-select" @change="handleNovelChange">
        <el-option v-for="novel in novelOptions" :key="novel.bookId" :label="`${novel.bookName} - ${novel.author}`" :value="novel.bookId" />
      </el-select>
    </div>

    <div class="content-layout">
      <div class="chart-panel">
        <div ref="chartRef" class="relation-chart"></div>
      </div>
      <div class="side-panel">
        <h3 class="panel-title"><el-icon><Connection /></el-icon> 相似作品列表</h3>
        <div class="similar-list">
          <div class="similar-item" v-for="(novel, index) in currentSimilarNovels" :key="novel.bookId">
            <div class="item-avatar" :style="{ background: avatarColors[index % avatarColors.length] }">
              {{ novel.bookName.charAt(0) }}
            </div>
            <div class="item-info">
              <div class="item-title">{{ novel.bookName }}</div>
              <div class="item-author">{{ novel.author }}</div>
              <div class="item-tags" v-if="novel.tags">
                <el-tag v-for="tag in novel.tags.split(',').slice(0, 2)" :key="tag" size="small" effect="plain" round>{{ tag.trim() }}</el-tag>
              </div>
            </div>
            <div class="item-score">
              <el-progress type="dashboard" :percentage="novel.similarity" :width="56" :stroke-width="4" :color="getSimilarityColor(novel.similarity)" />
              <span class="score-label">相似度</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Connection } from '@element-plus/icons-vue'
import request from '@/api/index'

const chartRef = ref(null)
let chartInstance = null

const avatarColors = [
  'linear-gradient(135deg, #667eea, #764ba2)',
  'linear-gradient(135deg, #f093fb, #f5576c)',
  'linear-gradient(135deg, #4facfe, #00f2fe)',
  'linear-gradient(135deg, #43e97b, #38f9d7)',
  'linear-gradient(135deg, #fa709a, #fee140)',
  'linear-gradient(135deg, #a18cd1, #fbc2eb)'
]

const novelOptions = ref([])
const selectedNovelId = ref(null)
const centerBook = ref(null)
const currentSimilarNovels = ref([])

const getSimilarityColor = (val) => {
  if (val >= 90) return '#67c23a'
  if (val >= 80) return '#409eff'
  if (val >= 70) return '#e6a23c'
  return '#909399'
}

const nodeColors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#a18cd1', '#4facfe', '#fa709a']

async function loadBookOptions() {
  try {
    const res = await request.get('/recommend/book-options')
    novelOptions.value = res.data || []
    if (novelOptions.value.length > 0 && !selectedNovelId.value) {
      selectedNovelId.value = novelOptions.value[0].bookId
      loadSimilar(selectedNovelId.value)
    }
  } catch (e) { /* keep empty */ }
}

async function loadSimilar(bookId) {
  try {
    const res = await request.get(`/recommend/similar/${bookId}`)
    const data = res.data || {}
    centerBook.value = data.center
    currentSimilarNovels.value = data.similar || []
    nextTick(() => initChart())
  } catch (e) { /* keep empty */ }
}

function handleNovelChange(bookId) {
  loadSimilar(bookId)
}

function initChart() {
  if (!chartRef.value || !centerBook.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)

  const centerNode = {
    name: centerBook.value.bookName,
    symbolSize: 70,
    itemStyle: { color: '#667eea', shadowBlur: 20, shadowColor: 'rgba(102, 126, 234, 0.5)' },
    label: { fontSize: 14, fontWeight: 'bold', color: '#303133' }
  }

  const similarNodes = currentSimilarNovels.value.map((novel, index) => ({
    name: novel.bookName,
    symbolSize: 36 + (novel.similarity || 0) * 0.25,
    itemStyle: { color: nodeColors[index % nodeColors.length], shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.15)' },
    label: { fontSize: 12, color: '#606266' }
  }))

  const links = currentSimilarNovels.value.map(novel => ({
    source: centerBook.value.bookName,
    target: novel.bookName,
    value: novel.similarity,
    lineStyle: { width: 1 + (novel.similarity || 0) / 30, color: (novel.similarity || 0) >= 50 ? '#409eff' : '#c0c4cc', curveness: 0.1 },
    label: { show: true, formatter: `${novel.similarity}%`, fontSize: 11, color: '#909399' }
  }))

  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: params => {
        if (params.dataType === 'node') return `<strong>${params.name}</strong>`
        if (params.dataType === 'edge') return `${params.data.source} → ${params.data.target}<br/>相似度: ${params.data.value}%`
        return ''
      }
    },
    series: [{
      type: 'graph', layout: 'force',
      force: { repulsion: 600, gravity: 0.1, edgeLength: [120, 250], layoutAnimation: true },
      roam: true, draggable: true, symbol: 'circle',
      data: [centerNode, ...similarNodes], links,
      label: { show: true, position: 'bottom', distance: 8 },
      edgeLabel: { show: true, fontSize: 11 },
      emphasis: { focus: 'adjacency', lineStyle: { width: 4 }, itemStyle: { shadowBlur: 20 } },
      lineStyle: { opacity: 0.7 }
    }]
  })
}

const handleResize = () => { chartInstance?.resize() }

onMounted(() => {
  loadBookOptions()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.similar-recommend-page { padding: $spacing-lg; background: $bg-page; min-height: calc(100vh - $top-nav-height); }
.page-header { margin-bottom: $spacing-lg; .page-title { font-size: 24px; font-weight: 700; color: $text-primary; margin-bottom: $spacing-xs; } .page-desc { font-size: 14px; color: $text-secondary; } }
.search-bar { margin-bottom: $spacing-lg; background: $bg-white; padding: $spacing-md $spacing-lg; border-radius: $border-radius-lg; box-shadow: $box-shadow-light; .novel-select { width: 400px; max-width: 100%; } }
.content-layout { display: flex; gap: $spacing-lg; align-items: flex-start; }
.chart-panel { flex: 1; background: $bg-white; border-radius: $border-radius-lg; box-shadow: $box-shadow-light; padding: $spacing-md; min-height: 520px; .relation-chart { width: 100%; height: 500px; } }
.side-panel {
  width: 360px; flex-shrink: 0; background: $bg-white; border-radius: $border-radius-lg; box-shadow: $box-shadow-light; padding: $spacing-lg; max-height: 560px; overflow-y: auto;
  &::-webkit-scrollbar { width: 4px; } &::-webkit-scrollbar-thumb { background: $border-color; border-radius: 2px; }
}
.panel-title { font-size: 16px; font-weight: 600; color: $text-primary; margin-bottom: $spacing-md; display: flex; align-items: center; gap: $spacing-sm; .el-icon { color: $primary-color; } }
.similar-list { display: flex; flex-direction: column; gap: $spacing-md; }

.similar-item {
  display: flex; align-items: center; gap: $spacing-md;
  padding: $spacing-md; border-radius: 12px; background: $bg-color;
  transition: all 0.25s ease;
  &:hover { background: #eaecf2; transform: translateX(4px); }
}

.item-avatar {
  width: 48px; height: 48px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 800; color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.item-info {
  flex: 1; min-width: 0;
  .item-title { font-size: 14px; font-weight: 600; color: $text-primary; margin-bottom: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .item-author { font-size: 12px; color: $text-secondary; margin-bottom: $spacing-xs; }
  .item-tags { display: flex; gap: $spacing-xs; flex-wrap: wrap; .el-tag { font-size: 10px; } }
}

.item-score {
  flex-shrink: 0; display: flex; flex-direction: column; align-items: center;
  .score-label { font-size: 10px; color: $text-secondary; margin-top: 2px; }
}

@media (max-width: 1024px) { .content-layout { flex-direction: column; } .side-panel { width: 100%; max-height: none; } }
</style>
