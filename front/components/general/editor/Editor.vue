<template>
  <v-container>
    <p style="color: #5e5e5e; font-size: 12px">
      Content
    </p>
    <draggable
      v-model="value"
      v-bind="dragOptions"
      @start="drag = true"
      @end="drag = false"
      class="list-group"
      handle=".hand"
    >
      <transition-group
        :name="!drag ? 'flip-list' : null"
        type="transition"
      >
        <v-row v-for="(element, index) in value" :key="element.id" align="center">
          <v-col sm="1" class="pa-1 hand text-center">
            <font-awesome-icon :icon="['fas', 'bars']" class="handle" />
          </v-col>
          <v-col cols="11" class="pa-1">
            <div v-if="element.type === 'p'">
              <TextEditor
                v-model="element.content"
                @removeBlock="value.splice(index, 1)"
                @hitEnter="addParagraph(index)"
              />
            </div>
            <div v-if="['file', 'image'].includes(element.type)">
              <v-row align="center">
                <v-col cols="11">
                  <MultiUpload
                    v-if="element.type === 'file'"
                    v-model="element.files"
                  />
                  <ImageUploader
                    v-if="element.type === 'image'"
                    v-model="element.files"
                  />
                </v-col>
                <v-col cols="1">
                  <CustomInsert @removeBlock="value.splice(index, 1)" disable-emoji disable-personalize removable />
                </v-col>
              </v-row>
            </div>
            <div v-if="['h1', 'h2', 'h3', 'quote', 'youtube', 'hr'].includes(element.type)">
              <TextEditor
                v-model="element.content"
                :root-element="element.type"
                @removeBlock="value.splice(index, 1)"
                @hitEnter="addParagraph(index)"
                disable-toolbar
              />
            </div>
            <div v-if="['ul', 'ol'].includes(element.type)">
              <v-row align="center">
                <v-col cols="11">
                  <ul v-if="element.type === 'ul'">
                    <TextEditor
                      v-for="i in element.items"
                      :key="i.id"
                      v-model="i.content"
                      :root-element="element.type"
                      @removeBlock="value.splice(index, 1)"
                      @hitEnter="addULItem(index)"
                    />
                  </ul>
                  <ol v-if="element.type === 'ol'">
                    <TextEditor
                      v-for="i in element.items"
                      :key="i.id"
                      v-model="i.content"
                      @removeBlock="value.splice(index, 1)"
                      @hitEnter="addULItem(index)"
                      root-element="ul"
                    />
                  </ol>
                </v-col>
                <v-col cols="1">
                  <CustomInsert
                    @removeBlock="value.splice(index, 1)"
                    @addItem="addULItem(index)"
                    disable-emoji
                    disable-personalize
                    removable
                    add-one
                  />
                </v-col>
              </v-row>
            </div>
          </v-col>
        </v-row>
      </transition-group>
    </draggable>
    <v-row class="mt-4">
      <v-menu offset-y>
        <template v-slot:activator="{ on }">
          <v-btn
            v-on="on"
            color="primary"
            dark
          >
            Add block type
          </v-btn>
        </template>
        <v-list>
          <v-list-item
            v-for="(item, index) in items"
            :key="index"
            @click="addItem(item)"
          >
            <v-list-item-title>{{ item.type }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-row>
  </v-container>
</template>

<script>
import draggable from 'vuedraggable'
import TextEditor from './TextEditor'
import MultiUpload from './MultiUpload'
import CustomInsert from './CustomInsert'
import ImageUploader from './ImageUploader'
export default {
  name: 'Editor',
  components: {
    TextEditor,
    draggable,
    MultiUpload,
    CustomInsert,
    ImageUploader
  },
  props: {
    value: {
      type: Array,
      required: true
    }
  },
  data: () => ({
    drag: false,
    menu: false,
    items: [
      { type: 'p', content: '' },
      { type: 'h1', content: '' },
      { type: 'h2', content: '' },
      { type: 'h3', content: '' },
      { type: 'quote', content: '' },
      { type: 'youtube', content: '' },
      { type: 'ul', items: [{ content: '', type: 'p' }] },
      { type: 'ol', items: [{ content: '', type: 'p' }] },
      { type: 'hr', content: '' },
      { type: 'file', content: '', files: [] },
      { type: 'image', content: '', files: [] }
    ],
    dragOptions: {
      animation: 200,
      group: 'description',
      disabled: false,
      ghostClass: 'ghost'
    },
    selectedItem: []
  }),
  watch: {
    value: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    }
  },
  mounted () {
    if (this.value.length === 0) {
      this.$emit('input', [{ type: 'p', content: '', id: this.getRandomString() }])
    } else {
      this.value.forEach((item) => {
        item.id = this.getRandomString()
      })
    }
  },
  methods: {
    addItem (item) {
      if (item.type === 'ul' || item.type === 'ol') {
        this.value.push({ type: item.type, items: JSON.parse(JSON.stringify(item.items)), id: this.getRandomString() })
        return
      }
      this.value.push({ type: item.type, content: item.content, id: this.getRandomString() })
    },
    addULItem (index) {
      this.value[index].items.push({ content: '', type: 'p' })
    },
    addParagraph (index) {
      this.value.splice(index + 1, 0, { type: 'p', content: '', id: this.getRandomString() })
    },
    getRandomString () {
      // from https://stackoverflow.com/a/6860916
      return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1)
    }
  }
}
</script>

<style scoped>
.flip-list-move {
  transition: transform 0.5s;
}
.no-move {
  transition: transform 0s;
}
.ghost {
  opacity: 0.5;
}
.list-group {
  min-height: 20px;
}
.list-group-item {
  cursor: move;
}
.list-group-item i {
  cursor: pointer;
}
.handle {
  font-size: 10px;
  vertical-align: center;
  cursor: pointer;
}
.v-btn {
  min-width: unset !important;
}
</style>
