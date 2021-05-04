<template>
  <div class="editor__content">
    <bubble-menu
      :tippy-options="{ duration: 100 }"
      :editor="editor"
      v-if="editor"
      class="bubble-menu"
    >
      <button @click="editor.chain().focus().toggleBold().run()" :class="{ 'is-active': editor.isActive('bold') }">
        Bold
      </button>
      <button @click="editor.chain().focus().toggleItalic().run()" :class="{ 'is-active': editor.isActive('italic') }">
        Italic
      </button>
      <button @click="editor.chain().focus().toggleStrike().run()" :class="{ 'is-active': editor.isActive('strike') }">
        Strike
      </button>
      <button @click="editor.chain().focus().toggleUnderline().run()" :class="{ 'is-active': editor.isActive('underline') }">
        Underline
      </button>
      <button @click="setLink" :class="{ 'is-active': editor.isActive('link') }">
        Link
      </button>
      <button @click="editor.chain().focus().unsetLink().run()" v-if="editor.isActive('link')">
        Remove
      </button>
    </bubble-menu>

    <floating-menu
      :tippy-options="{ duration: 100 }"
      :editor="editor"
      v-if="editor"
      class="floating-menu"
    >
      <button @click="editor.chain().focus().toggleHeading({ level: 1 }).run()" :class="{ 'is-active': editor.isActive('heading', { level: 1 }) }">
        H1
      </button>
      <button @click="editor.chain().focus().toggleHeading({ level: 2 }).run()" :class="{ 'is-active': editor.isActive('heading', { level: 2 }) }">
        H2
      </button>
      <button @click="editor.chain().focus().toggleBulletList().run()" :class="{ 'is-active': editor.isActive('bulletList') }">
        Bullet List
      </button>
      <button @click="editor.chain().focus().toggleOrderedList().run()" :class="{ 'is-active': editor.isActive('orderedList') }">
        Ordered List
      </button>
      <button @click="$refs.imageInput.click()" :class="{ 'is-active': editor.isActive('image') }">
        Image
      </button>
      <button @click="$refs.fileInput.click()" :class="{ 'is-active': editor.isActive('file') }">
        File
      </button>
      <button @click="$refs.videoInput.click()" :class="{ 'is-active': editor.isActive('video') }">
        Video
      </button>
      <button @click="editor.chain().focus().toggleBlockquote().run()" :class="{ 'is-active': editor.isActive('blockquote') }">
        Quote
      </button>
    </floating-menu>

    <input
      ref="imageInput"
      :accept="['image/jpg', 'image/jpeg', 'image/png']"
      @input="uploadImage"
      type="file"
      style="display:none"
    >
    <input
      ref="fileInput"
      @input="uploadFile"
      type="file"
      style="display:none"
    >
    <input
      ref="videoInput"
      @input="uploadVideo"
      type="file"
      style="display:none"
    >
    <editor-content :editor="editor" />
  </div>
</template>

<script>
import {
  Editor,
  EditorContent,
  BubbleMenu,
  FloatingMenu
} from '@tiptap/vue-2'
import { defaultExtensions } from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Underline from '@tiptap/extension-underline'
import OrderedList from '@tiptap/extension-ordered-list'
import Image from '@tiptap/extension-image'
import Blockquote from '@tiptap/extension-blockquote'
import { Video } from './VideoUploader.ts'
import { File } from './FileUploader.ts'

export default {
  components: {
    EditorContent,
    BubbleMenu,
    FloatingMenu
  },

  data: () => ({
    editor: null,
    content: ''
  }),
  props: {
    // eslint-disable-next-line
    value: {
      required: true
    }
  },
  watch: {
    '$store.state.refreshEditor' () {
      this.formatDataToEditorHTML(this.value)
    }
  },
  mounted () {
    const editor = new Editor({
      extensions: [
        ...defaultExtensions(),
        Link,
        Underline,
        OrderedList,
        Image,
        Blockquote,
        File,
        Video
      ],
      content: this.content
    })
    editor.on('update', ({ editor }) => {
      this.$emit('input', this.formatToData(editor.getJSON()))
    })
    this.editor = editor
    this.formatDataToEditorHTML(this.value)
  },
  methods: {
    uploadImage () {
      const item = this.$refs.imageInput.files[0]
      this.$org.getPreSignedURL({ name: item.name }).then((data) => {
        this.$org.uploadToAWS(data.url, item).then(() => {
          this.$org.confirmUploaded(data.id).then((fileItem) => {
            this.editor.chain().focus().setImage({ src: fileItem.file_url, alt: fileItem.id }).run()
          })
        })
      })
    },
    uploadVideo () {
      const item = this.$refs.videoInput.files[0]
      this.$org.getPreSignedURL({ name: item.name }).then((data) => {
        this.$org.uploadToAWS(data.url, item).then(() => {
          this.$org.confirmUploaded(data.id).then((fileItem) => {
            this.editor.chain().focus().addVideo({ src: fileItem.file_url, id: fileItem.id, type: 'video/' + fileItem.ext }).run()
          })
        })
      })
    },
    uploadFile () {
      const item = this.$refs.fileInput.files[0]
      this.$org.getPreSignedURL({ name: item.name }).then((data) => {
        this.$org.uploadToAWS(data.url, item).then(() => {
          this.$org.confirmUploaded(data.id).then((fileItem) => {
            this.editor.chain().focus().addFile({ name: fileItem.name, id: fileItem.id }).run()
            this.editor.chain().focus().setContent(fileItem.name)
          })
        })
      })
    },
    setLink () {
      const url = window.prompt('URL')
      this.editor.chain().focus().setLink({ href: url }).run()
    },
    paragraphToHTML (p) {
      let line = ''
      let link = ''
      p.content.forEach((one) => {
        let text = one.text
        if ('marks' in one) {
          if (one.marks.find(a => a.type === 'italic') !== undefined) {
            text = '<i>' + text + '</i>'
          }
          if (one.marks.find(a => a.type === 'code') !== undefined) {
            text = '<code>' + text + '</code>'
          }
          if (one.marks.find(a => a.type === 'bold') !== undefined) {
            text = '<b>' + text + '</b>'
          }
          if (one.marks.find(a => a.type === 'underline') !== undefined) {
            text = '<u>' + text + '</u>'
          }
          if (one.marks.find(a => a.type === 'strike') !== undefined) {
            text = '<strike>' + text + '</strike>'
          }
          if (one.marks.find(a => a.type === 'link') !== undefined) {
            link = one.marks.find(a => a.type === 'link').attrs.href
            text = '<a href="' + link + '">' + text + '</a>'
          }
        }
        line += text
      })
      return line
    },
    lineToHTML (items) {
      let line = ''
      let counter = 0
      items.content.forEach((paragraph) => {
        counter++
        line += this.paragraphToHTML(paragraph)
        if (counter < items.length) {
          line += '<br />'
        }
      })
      return line
    },
    formatToData (content) {
      const newValue = []
      content.content.forEach((one) => {
        console.log(one)
        if (one.type === 'paragraph') {
          if ('content' in one) {
            newValue.push({
              'type': 'p',
              'content': this.paragraphToHTML(one)
            })
          }
        }
        if (one.type === 'image') {
          if ('attrs' in one) {
            newValue.push({
              'type': 'image',
              'content': '',
              'files': [{ id: one.attrs.alt, file_url: one.attrs.src }]
            })
          }
        }
        if (one.type === 'file') {
          if ('attrs' in one) {
            newValue.push({
              'type': 'file',
              'content': '',
              'files': [{ id: one.attrs.id }]
            })
          }
        }
        if (one.type === 'video') {
          if ('attrs' in one) {
            newValue.push({
              'type': 'video',
              'content': '',
              'files': [{ id: one.attrs.id }]
            })
          }
        }
        if (one.type === 'blockquote') {
          if ('content' in one.content[0]) {
            newValue.push({
              'type': 'quote',
              'content': this.lineToHTML(one)
            })
          }
        }
        if (one.type === 'heading') {
          if ('content' in one) {
            newValue.push({
              'type': 'h' + one.attrs.level,
              'content': this.paragraphToHTML(one)
            })
          }
        }
        if (one.type === 'horizontal_rule') {
          newValue.push({
            'type': 'hr',
            'content': ''
          })
        }
        if (one.type === 'bulletList' || one.type === 'orderedList') {
          const listItems = []
          one.content.forEach((item) => {
            if ('content' in item.content[0]) {
              listItems.push({ 'content': this.lineToHTML(item) })
            }
          })
          newValue.push({
            'type': (one.type === 'orderedList') ? 'ol' : 'ul',
            'items': listItems,
            'content': ''
          })
        }
      })
      return newValue
    },
    formatDataToEditorHTML (value) {
      let html = ''
      console.log(value)
      value.forEach((one) => {
        if (one.type === 'p' && one.content !== '') {
          html += '<p>' + one.content + '</p>'
        }
        if (one.type === 'quote' && one.content !== '') {
          html += '<blockquote>' + one.content + '</blockquote>'
        }
        if (one.type === 'hr') {
          html += '<hr />'
        }
        if (one.type === 'h1' && one.content !== '') {
          html += '<h1>' + one.content + '</h1>'
        }
        if (one.type === 'image') {
          html += '<img src="' + one.files[0].file_url + '" alt="' + one.files[0].id + '" />'
        }
        if (one.type === 'file') {
          html += '<div name="' + one.files[0].name + '" id="' + one.files[0].id + '" disabled="true" class="file" draggable="true" contenteditable="false">' + one.files[0].name + '</div>'
        }
        if (one.type === 'video') {
          html += '<video src="' + one.files[0].file_url + '" id="' + one.files[0].id + '" controls="true" type="video/' + one.files[0].ext + '" draggable="true" class="ProseMirror-selectednode" contenteditable="false"></video>'
        }
        if (one.type === 'h2' && one.content !== '') {
          html += '<h2>' + one.content + '</h2>'
        }
        if (one.type === 'h3' && one.content !== '') {
          html += '<h3>' + one.content + '</h3>'
        }
        if ((one.type === 'ul' || one.type === 'ol') && one.items !== []) {
          html += '<' + one.type + '>'
          one.items.forEach((listItem) => {
            html += '<li>' + listItem.content + '</li>'
          })
          html += '</' + one.type + '>'
        }
      })
      console.log(html)
      this.editor.commands.setContent(html)
    }
  },
  beforeDestroy () {
    this.editor.destroy()
  }
}
</script>

<style lang="scss">
/* Basic editor styles */
$color-black: #000000;
$color-white: #ffffff;
$color-grey: #dddddd;
.ProseMirror {
  outline: 0;
  > * + * {
    margin-top: 0.75em;
  }

  ul,
  ol {
    padding: 0 1rem;
  }

  blockquote {
    padding-left: 1rem;
    border-left: 2px solid rgba(#0D0D0D, 0.1);
  }
}

.tippy-box {
  max-width: 400px !important;
}

.bubble-menu {
  display: flex;
  background-color: #0D0D0D;
  padding: 0.2rem;
  border-radius: 0.5rem;

  button {
    border: none;
    background: none;
    color: #FFF;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0 0.2rem;
    opacity: 0.6;

    &:hover,
    &.is-active {
      opacity: 1;
    }
  }
}

.floating-menu {
  display: flex;
  background-color: #0D0D0D10;
  padding: 0.2rem;
  border-radius: 0.5rem;

  button {
    border: none;
    background: none;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0 0.2rem;
    opacity: 0.6;

    &:hover,
    &.is-active {
      opacity: 1;
    }
  }
}
.editor {
  position: relative;
  &__content {
    overflow-wrap: break-word;
    word-wrap: break-word;
    word-break: break-word;
    * {
      caret-color: currentColor;
    }
    pre {
      padding: 0.7rem 1rem;
      border-radius: 5px;
      background: $color-black;
      color: $color-white;
      font-size: 0.8rem;
      overflow-x: auto;
      code {
        display: block;
      }
    }
    p code {
      padding: 0.2rem 0.4rem;
      border-radius: 5px;
      font-size: 0.8rem;
      font-weight: bold;
      background: rgba($color-black, 0.1);
      color: rgba($color-black, 0.8);
    }
    ul,
    ol {
      padding-left: 1rem;
    }
    li > p,
    li > ol,
    li > ul {
      margin: 0;
    }
    a {
      color: inherit;
    }
    blockquote {
      border-left: 3px solid rgba($color-black, 0.1);
      color: rgba($color-black, 0.8);
      padding-left: 0.8rem;
      font-style: italic;
      p {
        margin: 0;
      }
    }
    img {
      max-width: 100%;
      border-radius: 3px;
    }
    table {
      border-collapse: collapse;
      table-layout: fixed;
      width: 100%;
      margin: 0;
      overflow: hidden;
      td, th {
        min-width: 1em;
        border: 2px solid $color-grey;
        padding: 3px 5px;
        vertical-align: top;
        box-sizing: border-box;
        position: relative;
        > * {
          margin-bottom: 0;
        }
      }
      th {
        font-weight: bold;
        text-align: left;
      }
      .selectedCell:after {
        z-index: 2;
        position: absolute;
        content: "";
        left: 0; right: 0; top: 0; bottom: 0;
        background: rgba(200, 200, 255, 0.4);
        pointer-events: none;
      }
      .column-resize-handle {
        position: absolute;
        right: -2px; top: 0; bottom: 0;
        width: 4px;
        z-index: 20;
        background-color: #adf;
        pointer-events: none;
      }
    }
    .tableWrapper {
      margin: 1em 0;
      overflow-x: auto;
    }
    .resize-cursor {
      cursor: ew-resize;
      cursor: col-resize;
    }
  }
}
.file {
  background: rgba($color-black, 0.1);
  color: rgba($color-black, 0.6);
  font-size: 0.8rem;
  font-weight: bold;
  border-radius: 5px;
  padding: 0.2rem 0.5rem;
  white-space: nowrap;
}
</style>
