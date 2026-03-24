<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">主题分析</h2>
      <p class="page-desc">基于标签聚类的小说主题分布与关联分析</p>
    </div>

    <el-row :gutter="20">
      <el-col :span="15">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-header-title">主题聚类气泡图</span>
              <span class="card-header-hint">气泡大小代表相关小说数量，点击查看详情</span>
            </div>
          </template>
          <div ref="bubbleChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="detail-card">
          <template #header>
            <div class="card-header">
              <span class="card-header-title">主题详情</span>
            </div>
          </template>
          <div v-if="!selectedTopic" class="empty-detail">
            <el-empty description="点击左侧气泡查看主题详情" :image-size="120" />
          </div>
          <div v-else class="topic-detail">
            <div class="topic-header">
              <h3 class="topic-name">{{ selectedTopic.name }}</h3>
            </div>
            <el-descriptions :column="2" border size="small" class="topic-stats">
              <el-descriptions-item label="相关小说">{{ selectedTopic.novelCount }} 部</el-descriptions-item>
              <el-descriptions-item label="总字数">{{ (selectedTopic.totalWords / 100000000).toFixed(1) }}亿字</el-descriptions-item>
              <el-descriptions-item label="平均评分">{{ selectedTopic.avgRating }} 分</el-descriptions-item>
              <el-descriptions-item label="关联标签数">{{ selectedTopic.readerPercent }}</el-descriptions-item>
            </el-descriptions>
            <div class="topic-keywords">
              <h4>核心关键词</h4>
              <div class="keyword-tags">
                <el-tag v-for="kw in selectedTopic.keywords" :key="kw" size="small" effect="plain" class="keyword-tag">{{ kw }}</el-tag>
              </div>
            </div>
            <div class="top-novels">
              <h4>代表作品</h4>
              <div v-for="novel in selectedTopic.topNovels" :key="novel.title" class="novel-item">
                <div class="novel-info">
                  <span class="novel-title">{{ novel.title }}</span>
                  <span class="novel-author">{{ novel.author }}</span>
                </div>
                <div class="novel-rating">
                  <el-rate :model-value="novel.rating / 2" disabled show-score :score-template="`${novel.rating}`" size="small" />
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="comparison-card">
      <template #header>
        <div class="card-header"><span class="card-header-title">主题数据概览</span></div>
      </template>
      <el-table :data="topicList" stripe style="width: 100%">
        <el-table-column prop="name" label="主题名称" width="140">
          <template #default="{ row }">
            <span class="topic-name-cell" @click="selectTopic(row)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="novelCount" label="小说数量" align="center" sortable />
        <el-table-column label="总字数(亿)" align="center" sortable>
          <template #default="{ row }">
            {{ (row.totalWords / 100000000).toFixed(1) }}
          </template>
        </el-table-column>
        <el-table-column prop="avgRating" label="平均评分" align="center" sortable>
          <template #default="{ row }">
            <span :style="{ color: row.avgRating >= 8 ? '#67c23a' : row.avgRating >= 7 ? '#e6a23c' : '#f56c6c' }">{{ row.avgRating }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="readerPercent" label="关联标签数" align="center" sortable />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import request from '@/api/index'

const bubbleChartRef = ref(null)
let bubbleChart = null
const selectedTopic = ref(null)
const topicList = ref([])

function selectTopic(topic) { selectedTopic.value = topic }

async function loadTopics() {
  try {
    const res = await request.get('/analysis/topics')
    topicList.value = res.data || []
    initBubbleChart()
  } catch (e) { /* keep empty */ }
}

function initBubbleChart() {
  if (!bubbleChartRef.value || topicList.value.length === 0) return
  bubbleChart = echarts.init(bubbleChartRef.value)

  const colorPalette = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#9b59b6', '#1abc9c', '#e67e22', '#3f51b5', '#00bcd4', '#ff5722', '#8bc34a', '#795548', '#607d8b', '#cddc39', '#ff9800']

  const seriesData = topicList.value.map((topic, index) => ({
    name: topic.name,
    value: [topic.x, topic.y, topic.novelCount],
    symbolSize: Math.max(20, Math.sqrt(topic.novelCount) * 3),
    itemStyle: {
      color: new echarts.graphic.RadialGradient(0.5, 0.5, 0.5, [
        { offset: 0, color: colorPalette[index % colorPalette.length] + 'cc' },
        { offset: 1, color: colorPalette[index % colorPalette.length] + '66' }
      ]),
      borderColor: colorPalette[index % colorPalette.length], borderWidth: 2
    },
    label: { show: true, formatter: '{b}', fontSize: 13, fontWeight: 'bold', color: '#303133' }
  }))

  bubbleChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: params => {
        const topic = topicList.value.find(t => t.name === params.name)
        if (!topic) return ''
        return `<div style="font-weight:bold;margin-bottom:4px;">${topic.name}</div>
          <div>小说数量: ${topic.novelCount} 部</div>
          <div>平均评分: ${topic.avgRating} 分</div>`
      }
    },
    grid: { left: '8%', right: '8%', top: '8%', bottom: '8%' },
    xAxis: { type: 'value', min: 0, max: 500, axisLabel: { show: false }, axisLine: { show: false }, axisTick: { show: false }, splitLine: { lineStyle: { type: 'dashed', color: '#e4e7ed' } } },
    yAxis: { type: 'value', min: 0, max: 400, axisLabel: { show: false }, axisLine: { show: false }, axisTick: { show: false }, splitLine: { lineStyle: { type: 'dashed', color: '#e4e7ed' } } },
    series: [{ type: 'scatter', data: seriesData, emphasis: { scale: 1.2, itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0, 0, 0, 0.3)' } }, animationDuration: 1500, animationEasing: 'elasticOut' }]
  })

  bubbleChart.on('click', params => {
    const topic = topicList.value.find(t => t.name === params.name)
    if (topic) selectedTopic.value = topic
  })
}

function handleResize() { bubbleChart && bubbleChart.resize() }

onMounted(() => {
  loadTopics()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (bubbleChart) { bubbleChart.dispose(); bubbleChart = null }
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.page-container { padding: $spacing-lg; min-height: 100%; }
.page-header { margin-bottom: $spacing-lg; .page-title { font-size: 22px; font-weight: 600; color: $text-primary; margin: 0 0 $spacing-xs 0; } .page-desc { font-size: 14px; color: $text-secondary; margin: 0; } }
.card-header { display: flex; align-items: center; justify-content: space-between; .card-header-title { font-size: 16px; font-weight: 600; color: $text-primary; } .card-header-hint { font-size: 13px; color: $text-secondary; } }
.chart-card { margin-bottom: $spacing-lg; :deep(.el-card__body) { padding: $spacing-md; } }
.chart-container { width: 100%; height: 480px; }
.detail-card { margin-bottom: $spacing-lg; :deep(.el-card__body) { padding: $spacing-md; max-height: 540px; overflow-y: auto; } }
.empty-detail { display: flex; align-items: center; justify-content: center; min-height: 400px; }
.topic-detail {
  .topic-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: $spacing-md; .topic-name { font-size: 20px; font-weight: 600; color: $text-primary; margin: 0; } }
  .topic-stats { margin-bottom: $spacing-md; }
  .topic-keywords { margin-bottom: $spacing-md; h4 { font-size: 14px; font-weight: 600; color: $text-primary; margin: 0 0 $spacing-sm 0; } .keyword-tag { margin-right: $spacing-xs; margin-bottom: $spacing-xs; } }
  .top-novels {
    h4 { font-size: 14px; font-weight: 600; color: $text-primary; margin: 0 0 $spacing-sm 0; }
    .novel-item { display: flex; align-items: center; justify-content: space-between; padding: $spacing-sm $spacing-md; border-radius: $border-radius-sm; background: $bg-color; margin-bottom: $spacing-sm;
      .novel-info { display: flex; flex-direction: column; .novel-title { font-size: 14px; font-weight: 500; color: $text-primary; } .novel-author { font-size: 12px; color: $text-secondary; margin-top: 2px; } }
      .novel-rating { :deep(.el-rate) { height: 20px; } }
    }
  }
}
.comparison-card { margin-top: 0; .topic-name-cell { color: $primary-color; cursor: pointer; font-weight: 500; &:hover { text-decoration: underline; } } }
</style>
