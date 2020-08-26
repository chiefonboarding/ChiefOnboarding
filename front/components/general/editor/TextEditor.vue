<template>
  <div>
    <client-only>
      <v-row align="center">
        <v-col sm="11" class="py-0">
          <h1 @keyup.enter="$emit('hitEnter')" :class="id" v-if="rootElement === 'h1'" @mouseup="saveSelection" />
          <p @keyup.enter="$emit('hitEnter')" :class="id" v-if="rootElement === 'p'" @mouseup="saveSelection" class />
          <h2 @keyup.enter="$emit('hitEnter')" :class="id" v-if="rootElement === 'h2'" @mouseup="saveSelection" />
          <h3 @keyup.enter="$emit('hitEnter')" :class="id" v-if="rootElement === 'h3'" @mouseup="saveSelection" />
          <v-divider v-if="rootElement === 'hr'" />
          <iframe
            v-if="rootElement === 'youtube' && youtube !== ''"
            :src="youtube"
            width="560"
            height="315"
            frameborder="0"
            allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen
          />
          <p @keyup.enter="$emit('hitEnter')" :class="id" v-if="rootElement === 'youtube'" @mouseup="saveSelection" />
          <blockquote @keyup.enter="$emit('hitEnter')" :class="id" v-if="rootElement === 'quote'" @mouseup="saveSelection" />
          <li @keyup.enter="$emit('hitEnter')" :class="id" v-if="rootElement === 'ul'" @mouseup="saveSelection" />
        </v-col>
        <v-col sm="1" class="py-0">
          <CustomInsert @clickedEmoji="addExtra" @clickedPersonalize="addExtra" @removeBlock="$emit('removeBlock')" removable />
        </v-col>
      </v-row>
    </client-only>
  </div>
</template>

<script>
import MediumEditor from 'medium-editor'
import CustomInsert from './CustomInsert'
export default {
  name: 'TextEditor',
  components: { CustomInsert },
  props: {
    value: {
      type: String,
      default: ''
    },
    personalize: {
      type: Boolean,
      default: true
    },
    disableReturn: {
      type: Boolean,
      default: true
    },
    disableToolbar: {
      type: Boolean,
      default: false
    },
    rootElement: {
      type: String,
      default: 'p'
    },
    buttons: {
      type: Array,
      default: () => { return ['bold', 'italic', 'underline', 'anchor'] }
    }
  },
  data: () => ({
    editor: null,
    id: btoa(Math.random()).slice(0, 5),
    toolbar: {
      buttons: []
    }
  }),
  computed: {
    youtube () {
      // eslint-disable-next-line no-useless-escape
      const youtubeReg = /.*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]*).*/
      if (this.value.trim().match(youtubeReg) !== null && this.value.trim().match(youtubeReg).length === 2) {
        return 'https://youtube.com/embed/' + this.value.trim().match(youtubeReg)[1]
      }
      return ''
    }
  },
  mounted () {
    this.initialize()
  },
  methods: {
    initialize () {
      this.toolbar.buttons = this.buttons
      if (this.disableToolbar) {
        this.toolbar = false
      }
      setTimeout(() => {
        this.editor = new MediumEditor('.' + this.id, {
          toolbar: this.toolbar,
          disableReturn: this.disableReturn
        })
        this.editor.setContent(this.value)
        this.focus()
        this.editor.subscribe('editableInput', (event, editable) => {
          this.$emit('input', editable.innerHTML)
          this.editor.saveSelection()
        })
        // a bit of a dirty hack to put the personalization and emoji at the right place.
        this.editor.subscribe('focus', (event, editable) => {
          this.editor.restoreSelection()
        })
      }, 500)
    },
    focus () {
      document.getElementsByClassName(this.id)[0].focus()
    },
    addExtra (name) {
      this.focus()
      try {
        this.editor.cleanPaste(name)
      } catch {
        this.$store.dispatch('showSnackbar', 'Please focus first on the element, before adding something.')
      }
    },
    saveSelection () {
      this.editor.saveSelection()
    }
  }
}
</script>

<style scoped>
p {
  margin-bottom: 0px !important;
}
.medium-editor-element {
  min-height: 24px !important;
}
blockquote.medium-editor-element {
  min-height: 37px !important;
}
.medium-editor-element:focus {
  outline: none;
}
blockquote {
  background: #f9f9f9;
  border-left: 2px solid #ffbb42;
  padding: 0.5em 10px;
}
</style>
