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

// ==================== Mock Data ====================
const keywordTableData = ref([
  { keyword: '修仙', count: 18520, novelCount: 3240, tagType: '' },
  { keyword: '重生', count: 16890, novelCount: 2980, tagType: 'success' },
  { keyword: '穿越', count: 15430, novelCount: 2750, tagType: 'warning' },
  { keyword: '系统', count: 13870, novelCount: 2430, tagType: 'danger' },
  { keyword: '异能', count: 12650, novelCount: 2180, tagType: '' },
  { keyword: '都市', count: 11230, novelCount: 1960, tagType: 'success' },
  { keyword: '末日', count: 9870, novelCount: 1540, tagType: 'warning' },
  { keyword: '宫斗', count: 8940, novelCount: 1320, tagType: 'danger' },
  { keyword: '星际', count: 7860, novelCount: 1180, tagType: '' },
  { keyword: '校园', count: 7230, novelCount: 1050, tagType: 'success' },
  { keyword: '灵气复苏', count: 6580, novelCount: 920, tagType: 'warning' },
  { keyword: '无限流', count: 5940, novelCount: 860, tagType: 'danger' },
  { keyword: '快穿', count: 5320, novelCount: 780, tagType: '' },
  { keyword: '悬疑', count: 4870, novelCount: 710, tagType: 'success' },
  { keyword: '种田', count: 4350, novelCount: 640, tagType: 'warning' }
])

const novelList = ref([
  { id: 1, title: '凡人修仙传', author: '忘语', desc: '一个普通山村少年的修仙之旅，从凡人一步步走向仙途巅峰。', keywords: ['修仙', '系统', '灵气复苏'], type: '仙侠', wordCount: 780 },
  { id: 2, title: '重生之都市修仙', author: '十月流年', desc: '重生回到高中时代，开启了一段全新的修仙人生。', keywords: ['重生', '修仙', '都市'], type: '都市', wordCount: 450 },
  { id: 3, title: '穿越星际之路', author: '星河万里', desc: '穿越到星际时代，凭借前世记忆在星际中闯出一片天地。', keywords: ['穿越', '星际', '异能'], type: '科幻', wordCount: 380 },
  { id: 4, title: '末日系统降临', author: '暗夜行者', desc: '末日来临，获得神秘系统，在废土世界中挣扎求生。', keywords: ['末日', '系统', '异能'], type: '末世', wordCount: 520 },
  { id: 5, title: '宫斗之凤谋天下', author: '月落星沉', desc: '重生后的她不再隐忍，以智谋和手段步步为营，登上权力巅峰。', keywords: ['宫斗', '重生', '穿越'], type: '古言', wordCount: 310 },
  { id: 6, title: '校园异能王', author: '青春无悔', desc: '一觉醒来获得超能力的高中生，在校园中开启奇妙冒险。', keywords: ['校园', '异能', '系统'], type: '都市', wordCount: 280 },
  { id: 7, title: '无限流之万界归来', author: '无尽幻想', desc: '穿梭于不同副本世界，收集力量，揭开无限空间的终极秘密。', keywords: ['无限流', '穿越', '系统'], type: '科幻', wordCount: 610 },
  { id: 8, title: '灵气复苏之巅峰', author: '东方不败', desc: '当灵气席卷全球，普通人也有机会踏上修仙之路。', keywords: ['灵气复苏', '修仙', '都市'], type: '玄幻', wordCount: 430 },
  { id: 9, title: '快穿之炮灰逆袭', author: '糖果甜心', desc: '绑定系统穿梭各个小世界，完成任务逆袭人生。', keywords: ['快穿', '穿越', '系统'], type: '言情', wordCount: 350 },
  { id: 10, title: '悬疑之迷雾追踪', author: '冷面书生', desc: '天才侦探携手法医，抽丝剥茧揭开一桩桩惊天大案。', keywords: ['悬疑', '都市'], type: '悬疑', wordCount: 270 },
  { id: 11, title: '种田之悠然南山', author: '田园牧歌', desc: '穿越到古代乡村，靠种田发家致富，过上悠闲田园生活。', keywords: ['种田', '穿越', '重生'], type: '古言', wordCount: 220 },
  { id: 12, title: '星际机甲风暴', author: '钢铁洪流', desc: '在星际联邦时代，驾驶机甲征战星海，守护人类文明。', keywords: ['星际', '异能', '系统'], type: '科幻', wordCount: 490 }
])

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
  initWordCloud()
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
