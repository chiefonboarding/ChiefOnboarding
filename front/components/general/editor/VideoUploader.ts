import {
  Node,
  Command,
  nodeInputRule,
  mergeAttributes
} from '@tiptap/core'

declare module '@tiptap/core' {
  interface Commands {
    video: {
      addVideo: (options: { url: string, id: number, type: string }) => Command,
    }
  }
}

export const inputRegex = /!\[(.+|:?)]\((\S+)(?:(?:\s+)["'](\S+)["'])?\)/
export const Video = Node.create({
  name: 'video',

  defaultOptions: {
    inline: false,
    HTMLAttributes: {}
  },

  inline () {
    return this.options.inline
  },

  group () {
    return this.options.inline ? 'inline' : 'block'
  },

  draggable: true,

  addAttributes () {
    return {
      src: {
        default: null
      },
      id: {
        default: null
      },
      controls: {
        default: true
      },
      type: {
        default: null
      }
    }
  },

  parseHTML () {
    return [
      {
        tag: 'video'
      }
    ]
  },

  renderHTML ({ HTMLAttributes }) {
    return ['video', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), ['source', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes)]]
  },

  addCommands () {
    return {
      addVideo: options => ({ tr, dispatch }) => {
        console.info(options)
        const { selection } = tr
        const node = this.type.create(options)

        if (dispatch) {
          tr.replaceRangeWith(selection.from, selection.to, node)
        }

        return true
      }
    }
  },

  addInputRules () {
    return [
      nodeInputRule(inputRegex, this.type, (match) => {
        const [, src, id, type] = match

        return { src, id, type }
      })
    ]
  }
})
