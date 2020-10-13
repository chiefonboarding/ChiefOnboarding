import { Node } from 'tiptap'
import { nodeInputRule } from 'tiptap-commands'

/**
 * Matches following attributes in Markdown-typed image: [, alt, src, title]
 *
 * Example:
 * ![Lorem](image.jpg) -> [, "Lorem", "image.jpg"]
 * ![](image.jpg "Ipsum") -> [, "", "image.jpg", "Ipsum"]
 * ![Lorem](image.jpg "Ipsum") -> [, "Lorem", "image.jpg", "Ipsum"]
 */
const IMAGE_INPUT_REGEX = /!\[(.+|:?)]\((\S+)(?:(?:\s+)["'](\S+)["'])?\)/

export default class Image extends Node {
  get name () {
    return 'image'
  }

  get schema () {
    return {
      inline: false,
      attrs: {
        src: {},
        id: -1,
        alt: {
          default: null
        },
        title: {
          default: null
        }
      },
      group: 'block',
      draggable: true,
      parseDOM: [
        {
          tag: 'img[src]',
          getAttrs: dom => ({
            src: dom.getAttribute('src'),
            title: dom.getAttribute('title'),
            alt: dom.getAttribute('alt'),
            id: dom.getAttribute('id')
          })
        }
      ],
      toDOM: node => ['img', node.attrs]
    }
  }

  commands ({ type }) {
    return attrs => (state, dispatch) => {
      const { selection } = state
      const position = selection.$cursor ? selection.$cursor.pos : selection.$to.pos
      const node = type.create(attrs)
      const transaction = state.tr.insert(position, node)
      dispatch(transaction)
    }
  }

  inputRules ({ type }) {
    return [
      nodeInputRule(IMAGE_INPUT_REGEX, type, (match) => {
        const [, alt, src, title, id] = match
        return {
          src,
          alt,
          title,
          id
        }
      })
    ]
  }
}
