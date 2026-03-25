<template>
  <div class="search-page">
    <div class="search-header">
      <h2>搜索结果：<span class="keyword">{{ keyword }}</span></h2>
      <p class="result-count">共找到 <strong>{{ totalResults }}</strong> 条相关结果</p>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="全部" name="all">
        <div class="result-list">
          <el-card v-for="item in allResults" :key="item.id" shadow="hover" class="result-item">
            <div class="result-content">
              <el-tag size="small" :type="item.tagType">{{ item.category }}</el-tag>
              <h3 class="result-title">{{ item.title }}</h3>
              <p class="result-desc">{{ item.desc }}</p>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <el-tab-pane label="小说" name="novel">
        <div class="novel-list">
          <div v-for="item in novelResults" :key="item.id" class="novel-item">
            <div class="novel-cover" :style="{ background: item.gradient }"></div>
            <div class="novel-info">
              <h3>{{ item.title }}</h3>
              <p>作者：{{ item.author }}</p>
              <div class="novel-meta">
                <el-tag size="small">{{ item.type }}</el-tag>
                <el-rate :model-value="item.score" disabled show-score size="small" />
              </div>
              <p class="novel-desc">{{ item.desc }}</p>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="作者" name="author">
        <el-row :gutter="16">
          <el-col :span="8" v-for="item in authorResults" :key="item.id">
            <el-card shadow="hover" class="author-card">
              <div class="author-info">
                <el-avatar :size="48" :icon="UserFilled" />
                <div>
                  <h4>{{ item.name }}</h4>
                  <p>{{ item.novelCount }} 部作品</p>
                </div>
              </div>
              <div class="author-works">
                <el-tag v-for="w in item.works" :key="w" size="small" effect="plain">{{ w }}</el-tag>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="标签" name="tag">
        <div class="tag-cloud">
          <el-tag
            v-for="tag in tagResults"
            :key="tag.name"
            :style="{ fontSize: tag.size + 'px' }"
            class="tag-item"
            effect="plain"
          >
            {{ tag.name }} ({{ tag.count }})
          </el-tag>
        </div>
      </el-tab-pane>
    </el-tabs>

    <div class="pagination-wrapper">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="totalResults"
        :page-size="10"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { UserFilled } from '@element-plus/icons-vue'
import request from '@/api/index'

const route = useRoute()
const keyword = computed(() => route.query.q || '')
const activeTab = ref('all')
const totalResults = ref(0)

const allResults = ref([])
const novelResults = ref([])
const authorResults = ref([])
const tagResults = ref([])

async function doSearch() {
  if (!keyword.value) return
  try {
    const res = await request.get('/search', { params: { keyword: keyword.value } })
    const books = res.data || []
    totalResults.value = books.length
    // 全部结果
    allResults.value = books.map(b => ({
      id: b.bookId, category: b.category || '小说', tagType: '', title: b.bookName,
      desc: b.bookAbstract || `作者: ${b.author || '未知'} | 评分: ${b.score || 0} | ${b.tags || ''}`
    }))
    // 小说tab
    novelResults.value = books.map(b => ({
      id: b.bookId, title: b.bookName, author: b.author || '未知', type: b.category || '其他',
      score: Math.min((b.score || 0) / 2, 5), gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
      desc: b.bookAbstract || ''
    }))
    // 作者tab（去重聚合）
    const authorMap = {}
    books.forEach(b => {
      if (!b.author) return
      if (!authorMap[b.author]) authorMap[b.author] = { name: b.author, works: [] }
      if (authorMap[b.author].works.length < 3) authorMap[b.author].works.push(b.bookName)
    })
    authorResults.value = Object.values(authorMap).map((a, i) => ({
      id: i, name: a.name, novelCount: a.works.length, works: a.works
    }))
    // 标签tab
    const tagMap = {}
    books.forEach(b => {
      if (!b.tags) return
      b.tags.split(',').forEach(t => {
        t = t.trim()
        if (t) tagMap[t] = (tagMap[t] || 0) + 1
      })
    })
    tagResults.value = Object.entries(tagMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)
      .map(([name, count]) => ({ name, count, size: Math.min(12 + count * 2, 24) }))
  } catch (e) { /* 拦截器已处理 */ }
}

watch(keyword, () => doSearch(), { immediate: true })
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.search-page {
  padding: $spacing-lg;
  min-height: 100%;
}

.search-header {
  margin-bottom: $spacing-lg;

  h2 {
    font-size: 20px;
    color: $text-primary;
    margin: 0 0 $spacing-xs 0;

    .keyword { color: $primary-color; }
  }

  .result-count {
    font-size: 13px;
    color: $text-secondary;
    margin: 0;
  }
}

.result-list {
  .result-item {
    margin-bottom: $spacing-md;
    cursor: pointer;
  }

  .result-title {
    font-size: 16px;
    color: $text-primary;
    margin: $spacing-sm 0 $spacing-xs;
  }

  .result-desc {
    font-size: 13px;
    color: $text-secondary;
    margin: 0;
    line-height: 1.6;
  }
}

.novel-list {
  .novel-item {
    display: flex;
    gap: $spacing-md;
    padding: $spacing-md;
    background: $bg-white;
    border-radius: $border-radius-md;
    box-shadow: $box-shadow-light;
    margin-bottom: $spacing-md;
    cursor: pointer;

    &:hover { box-shadow: $box-shadow; }
  }

  .novel-cover {
    width: 100px;
    height: 140px;
    border-radius: $border-radius-sm;
    flex-shrink: 0;
  }

  .novel-info {
    flex: 1;

    h3 { margin: 0 0 $spacing-xs; font-size: 16px; color: $text-primary; }
    p { margin: 0 0 $spacing-xs; font-size: 13px; color: $text-secondary; }
  }

  .novel-meta {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    margin-bottom: $spacing-xs;
  }

  .novel-desc {
    line-height: 1.6;
  }
}

.author-card {
  margin-bottom: $spacing-md;

  .author-info {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    margin-bottom: $spacing-md;

    h4 { margin: 0; font-size: 15px; }
    p { margin: 4px 0 0; font-size: 13px; color: $text-secondary; }
  }

  .author-works {
    display: flex;
    gap: $spacing-xs;
    flex-wrap: wrap;
  }
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-md;
  padding: $spacing-lg;

  .tag-item {
    cursor: pointer;
    transition: all 0.3s;

    &:hover { transform: scale(1.1); }
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: $spacing-lg 0;
}
</style>
