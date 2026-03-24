<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">关键词分析</h2>
      <p class="page-desc">基于小说文本挖掘的高频关键词统计与关联分析</p>
    </div>

    <el-row :gutter="20" class="top-section">
      <!-- 左侧：词云 -->
      <el-col :span="14">
        <div class="card-box">
          <div class="card-box-header">
            <span class="card-box-title">关键词词云</span>
          </div>
          <div ref="wordCloudRef" class="chart-container"></div>
        </div>
      </el-col>

      <!-- 右侧：排名表格 -->
      <el-col :span="10">
        <div class="card-box">
          <div class="card-box-header">
            <span class="card-box-title">关键词排名</span>
          </div>
          <div class="table-wrapper">
            <el-table
              :data="keywordTableData"
              stripe
              highlight-current-row
              @row-click="handleKeywordClick"
              style="width: 100%"
              size="default"
            >
              <el-table-column label="排名" width="70" align="center">
                <template #default="{ $index }">
                  <span
                    class="rank-badge"
                    :class="{ 'rank-top': $index < 3 }"
                  >
                    {{ $index + 1 }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="keyword" label="关键词" align="center">
                <template #default="{ row }">
                  <el-tag
                    :type="row.tagType"
                    effect="plain"
                    size="small"
                  >
                    {{ row.keyword }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="出现次数" align="center" sortable />
              <el-table-column prop="novelCount" label="相关小说数" align="center" sortable />
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 底部：联动小说列表 -->
    <div class="card-box novel-section">
      <div class="card-box-header">
        <span class="card-box-title">
          联动小说列表
          <el-tag v-if="selectedKeyword" type="primary" effect="dark" size="small" closable @close="clearSelection" style="margin-left: 10px;">
            {{ selectedKeyword }}
          </el-tag>
          <span v-else class="hint-text">（点击关键词或表格行筛选小说）</span>
        </span>
      </div>
      <div class="novel-list">
        <el-row :gutter="16">
          <el-col
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
            v-for="novel in filteredNovels"
            :key="novel.id"
          >
            <el-card shadow="hover" class="novel-card">
              <div class="novel-card-body">
                <h4 class="novel-title">{{ novel.title }}</h4>
                <p class="novel-author">{{ novel.author }}</p>
                <p class="novel-desc">{{ novel.desc }}</p>
                <div class="novel-tags">
                  <el-tag
                    v-for="tag in novel.keywords"
                    :key="tag"
                    size="small"
                    :type="tag === selectedKeyword ? 'primary' : 'info'"
                    effect="plain"
                    class="novel-tag"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
                <div class="novel-meta">
                  <span>{{ novel.type }}</span>
                  <span>{{ novel.wordCount }}万字</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-empty v-if="filteredNovels.length === 0" description="暂无匹配小说" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import request from '@/api/index'

// ==================== Data ====================
const keywordTableData = ref([])
const novelList = ref([])

async function loadKeywords() {
  try {
    const res = await request.get('/analysis/keywords')
    keywordTableData.value = (res.data || []).map((item, i) => ({
      keyword: item.name,
      count: item.value,
      novelCount: item.value,
      tagType: ['', 'success', 'warning', 'danger'][i % 4]
    }))
    initWordCloud()
  } catch (e) { /* 保持空 */ }
}

async function loadBooksByTag(tag) {
  try {
    const res = await request.get('/analysis/keywords/books', { params: { tag } })
    novelList.value = (res.data || []).map(b => ({
      id: b.bookId,
      title: b.bookName,
      author: b.author || '未知',
      desc: b.bookAbstract || b.tags || '',
      keywords: b.tags ? b.tags.split(',').map(t => t.trim()) : [],
      type: b.category || '其他',
      wordCount: b.wordNumber ? Math.round(b.wordNumber / 10000) : 0
    }))
  } catch (e) { /* 保持空 */ }
}

// ==================== State ====================
const wordCloudRef = ref(null)
let wordCloudChart = null
const selectedKeyword = ref('')

const filteredNovels = computed(() => {
  if (!selectedKeyword.value) return novelList.value
  return novelList.value.filter(novel =>
    novel.keywords.includes(selectedKeyword.value)
  )
})

// ==================== Methods ====================
function handleKeywordClick(row) {
  selectedKeyword.value = row.keyword
  loadBooksByTag(row.keyword)
}

function clearSelection() {
  selectedKeyword.value = ''
}

function initWordCloud() {
  if (!wordCloudRef.value) return
  wordCloudChart = echarts.init(wordCloudRef.value)

  const wordData = keywordTableData.value.map(item => ({
    name: item.keyword,
    value: item.count
  }))

  const option = {
    tooltip: {
      show: true,
      formatter: (params) => {
        return `<b>${params.name}</b><br/>出现次数: ${params.value.toLocaleString()}`
      }
    },
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      left: 'center',
      top: 'center',
      width: '90%',
      height: '90%',
      sizeRange: [18, 60],
      rotationRange: [-45, 45],
      rotationStep: 15,
      gridSize: 10,
      drawOutOfBound: false,
      layoutAnimation: true,
      textStyle: {
        fontFamily: 'Microsoft YaHei, sans-serif',
        fontWeight: 'bold',
        color: () => {
          const colors = [
            '#409eff', '#67c23a', '#e6a23c', '#f56c6c',
            '#909399', '#3a8ee6', '#85ce61', '#ebb563',
            '#f78989', '#a6a9ad', '#66b1ff', '#b3e19d'
          ]
          return colors[Math.floor(Math.random() * colors.length)]
        }
      },
      emphasis: {
        textStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.25)'
        }
      },
      data: wordData
    }]
  }

  wordCloudChart.setOption(option)
  wordCloudChart.on('click', (params) => {
    selectedKeyword.value = params.name
  })
}

function handleResize() {
  wordCloudChart && wordCloudChart.resize()
}

// ==================== Lifecycle ====================
onMounted(() => {
  loadKeywords()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (wordCloudChart) {
    wordCloudChart.dispose()
    wordCloudChart = null
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

      .hint-text {
        font-size: 13px;
        color: $text-secondary;
        font-weight: 400;
      }
    }
  }
}

.top-section {
  margin-bottom: 0;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.table-wrapper {
  max-height: 400px;
  overflow-y: auto;

  :deep(.el-table) {
    cursor: pointer;
  }
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  background: $bg-color;
  color: $text-regular;

  &.rank-top {
    background: $primary-color;
    color: #fff;
  }
}

.novel-section {
  .novel-list {
    margin-top: $spacing-sm;
  }
}

.novel-card {
  margin-bottom: $spacing-md;
  transition: transform 0.2s;

  &:hover {
    transform: translateY(-2px);
  }

  .novel-card-body {
    .novel-title {
      font-size: 15px;
      font-weight: 600;
      color: $text-primary;
      margin: 0 0 $spacing-xs 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .novel-author {
      font-size: 13px;
      color: $text-secondary;
      margin: 0 0 $spacing-sm 0;
    }

    .novel-desc {
      font-size: 13px;
      color: $text-regular;
      margin: 0 0 $spacing-sm 0;
      line-height: 1.5;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .novel-tags {
      margin-bottom: $spacing-sm;

      .novel-tag {
        margin-right: $spacing-xs;
        margin-bottom: $spacing-xs;
      }
    }

    .novel-meta {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: $text-secondary;
    }
  }
}
</style>
