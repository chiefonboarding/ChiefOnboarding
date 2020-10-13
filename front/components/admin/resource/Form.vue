<template>
  <v-container class="pa-4">
    <v-row>
      <v-col cols="4" class="py-0">
        <v-col cols="12" class="py-0">
          <VTextFieldEmoji
            v-model="value.name"
            :label="$t('forms.title')"
            :errors="errorMessages.name"
            @removeError="errorMessages.name=''"
          />
        </v-col>
        <v-col cols="12" class="py-0">
          <TagsSelector v-model="value.tags" class="pt-2" />
        </v-col>
        <v-col cols="12" class="py-0">
          <label> {{ $t('resource.chapters') }}</label>
          <v-treeview
            :items="value.chapters"
            :active.sync="tree"
            activatable
            item-key="id"
            item-children="chapters"
          >
            <template v-slot:prepend="{ item }">
              <font-awesome-icon v-if="item.type === 1" :icon="['far', 'folder']" />
              <font-awesome-icon v-else-if="item.type === 2" :icon="['far', 'question-circle']" />
              <font-awesome-icon v-else :icon="['far', 'file']" />
            </template>
            <template v-slot:append="{ item }">
              <ResourceOptions
                @removeItem="removeItem(item)"
                @moveUp="move(item, -1)"
                @moveDown="move(item, 1)"
                @add="add(item, ...arguments)"
              />
            </template>
          </v-treeview>
        </v-col>
        <v-col class="py-0">
          <v-combobox
            v-model="value.category"
            :items="$store.state.categories"
            :label="$t('resource.cat')"
          />
        </v-col>
        <v-col cols="12" class="py-0">
          <v-switch
            v-model="value.course"
            :label="$t('resource.thisIsACourse')"
            class="mt-0"
          />
        </v-col>
        <v-col v-if="value.course" cols="12" class="py-0">
          <v-text-field
            v-model="value.on_day"
            :label="$t('resource.dueOnWorkday')"
            :error-messages="errorMessages.when"
            @keyup="errorMessages.when=''"
            type="number"
          />
        </v-col>
      </v-col>
      <v-col cols="8" class="py-0">
        <VTextFieldEmoji
          v-model="chapter.name"
          :label="$t('resource.chapterTitle')"
        />
        <v-col v-if="!('content' in chapter)" cols="12" class="pa-0">
          <p>Please select a page or question part</p>
        </v-col>
        <v-col v-else-if="chapter.type === 1" cols="12" class="pa-0">
          <p>You can only change the title of a folder.</p>
        </v-col>
        <v-col v-else cols="12" class="pa-0">
          <div v-if="chapter.type === 0">
            <Editor v-model="chapter.content" ref="edit" />
          </div>
          <ResourceQuestions v-model="chapter.content" v-else />
        </v-col>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import ResourceQuestions from './ResourceQuestions'
import ResourceOptions from './ResourceOptions'
export default {
  components: { ResourceOptions, ResourceQuestions },
  props: {
    value: {
      type: Object,
      default: () => { return { resources: [] } }
    },
    errors: {
      type: Object,
      required: true
    },
    inline: {
      type: Boolean,
      default: false
    }
  },
  data: vm => ({
    tree: [],
    search: '',
    panel: 1,
    chapterId: 1,
    innerChapter: -1,
    doNotChange: false,
    chapter: {},
    parent: []
  }),
  computed: {
    errorMessages () {
      return JSON.parse(JSON.stringify(this.errors))
    }
  },
  watch: {
    value: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    },
    tree (value) {
      this.getChapter()
    },
    errors (value) {
      if ('content' in value) {
        this.$store.dispatch('showSnackbar', 'Content: ' + value.content[0])
      }
    }
  },
  mounted () {
    this.chapter = this.value.chapters[0]
    this.tree = [this.value.chapters[0].id]
    if (this.value.course) {
      this.panel = [true, true]
    }
  },
  methods: {
    move (item, upOrDown) {
      this.findParent(this.value.chapters, item.id)
      const oldIndex = this.parent.findIndex(a => a.id === item.id)
      // check if new index exists
      if ((oldIndex + 1 === this.parent.length && upOrDown === 1) || (oldIndex === 0 && upOrDown === -1)) { return }
      this.parent.splice(oldIndex, 1)
      this.parent.splice(oldIndex + upOrDown, 0, item)
    },
    getChapter () {
      this.findParent(this.value.chapters, this.tree[0])
      this.chapter = (this.parent === null) ? {} : this.parent.find(a => a.id === this.tree[0])
      if (this.$refs.edit !== undefined && 'content' in this.chapter) {
        this.$refs.edit.formatDataToEditorHTML(this.chapter.content)
      }
    },
    add (item, contentType) {
      this.findParent(this.value.chapters, item.id)
      const index = this.parent.findIndex(a => a.id === item.id)
      const newItem = {
        id: this.getRandomString(),
        type: contentType,
        name: 'New item',
        content: [],
        files: []
      }
      if (contentType === 1) {
        newItem.chapters = [{
          id: this.getRandomString(),
          type: 0,
          name: 'New item',
          content: [],
          files: []
        }]
      }
      this.parent.splice(index + 1, 0, newItem)
    },
    removeItem (item) {
      this.findParent(this.value.chapters, item.id)
      if (this.parent.length === 1) {
        this.$store.dispatch('showSnackbar', 'You can\'t delete the last item.')
        return
      }
      const indexAt = this.parent.findIndex(a => a.id === item.id)
      this.parent.splice(indexAt, 1)
    },
    findParent (source, id) {
      // https://stackoverflow.com/a/23460304
      if (id === undefined) {
        this.parent = null
        return
      }
      let key
      for (key in source) {
        const item = source[key]
        if (item.id === id) {
          this.parent = source
          return
        }
        if (item.chapters) {
          const subresult = this.findParent(item.chapters, id)
          if (subresult) {
            this.parent = item.chapters
            return
          }
        }
      }
      return null
    },
    getRandomString () {
      // from https://stackoverflow.com/a/6860916
      return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1)
    }
  }
}
</script>
