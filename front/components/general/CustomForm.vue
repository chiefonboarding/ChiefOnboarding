<template>
  <v-container>
    <v-row style="width: 100%">
      <v-col sm="12">
        <p style="color: #5e5e5e; font-size: 12px">
          {{ $t('form.options') }}
        </p>
      </v-col>
      <v-col v-if="!value.length" sm="12" style="color: #5e5e5e; font-size: 12px">
        {{ $t('form.noItems') }}
      </v-col>
      <v-col v-else sm="12">
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
            <v-row v-for="(i, index) in value" :key="i.id" align="center">
              <v-col sm="1" class="pa-1 hand text-center">
                <font-awesome-icon :icon="['fas', 'bars']" class="handle" />
              </v-col>
              <v-col v-if="i.type === 'input'" sm="11">
                <v-text-field
                  v-model="i.text"
                  :label="$store.state.org.slack_key ? $t('form.smallTextSlack') : $t('form.smallText')"
                  :hide-details="!$store.state.org.slack_key"
                  :counter="$store.state.org.slack_key ? 48 : undefined"
                  @click:append="value.splice(index, 1)"
                  filled
                  style="margin-bottom: 1px;"
                  append-icon="close"
                />
              </v-col>
              <v-col v-if="i.type === 'upload'" sm="11">
                <v-text-field
                  v-model="i.text"
                  :label="$t('form.fileUpload')"
                  :counter="$store.state.org.slack_key ? 48 : undefined"
                  @click:append="value.splice(index, 1)"
                  filled
                  hide-details
                  style="margin-bottom: 1px;"
                  append-icon="close"
                />
              </v-col>
              <v-col v-if="i.type === 'text'" sm="11">
                <v-text-field
                  v-model="i.text"
                  :label="$store.state.org.slack_key ? $t('form.largeTextSlack') : $t('form.largeText')"
                  :hide-details="!$store.state.org.slack_key"
                  :counter="$store.state.org.slack_key ? 48 : undefined"
                  @click:append="value.splice(index, 1)"
                  filled
                  append-icon="close"
                />
              </v-col>
              <v-col v-if="i.type === 'check'" sm="11">
                <v-text-field
                  v-model="i.text"
                  :label="$t('form.checkboxGroupName')"
                  @click:append="value.splice(index, 1)"
                  filled
                  hide-details
                  append-icon="close"
                />
                <div v-for="(j, index_) in i.items" :key="index_" style="margin-left: 20px;">
                  <v-text-field
                    v-model="j.name"
                    :label="$t('form.checkboxItemName')"
                    @click:append="i.items.splice(index_, 1)"
                    filled
                    hide-details
                    append-icon="close"
                  />
                </div>
                <v-btn @click="addSubItem(i.items)" depressed style="margin-left: 20px; margin-top: 5px;">
                  {{ $t('buttons.add') }}
                </v-btn>
              </v-col>
              <v-col v-if="i.type === 'select'" sm="11">
                <v-text-field
                  v-model="i.text"
                  :label="$store.state.org.slack_key ? $t('form.comboBoxSlack') : $t('form.comboBox')"
                  :hide-details="!$store.state.org.slack_key"
                  :counter="$store.state.org.slack_key ? 48 : undefined"
                  @click:append="value.splice(index, 1)"
                  filled
                  append-icon="close"
                />
                <div v-for="(j, index_) in i.options" :key="j.id" style="margin-left: 20px;">
                  <v-text-field
                    v-model="j.name"
                    :label="$store.state.org.slack_key ? $t('form.optionSlack') : $t('form.option')"
                    :hide-details="!$store.state.org.slack_key"
                    :counter="$store.state.org.slack_key ? 75 : undefined"
                    @click:append="i.options.splice(index_, 1)"
                    filled
                    append-icon="close"
                  />
                </div>
                <v-btn @click="addSubItem(i.options)" depressed style="margin-left: 20px;margin-top: 10px">
                  {{ $t('buttons.add') }}
                </v-btn>
              </v-col>
            </v-row>
          </transition-group>
        </draggable>
      </v-col>
    </v-row>
    <v-row>
      <v-col align="center">
        <v-chip
          v-for="item in items"
          :key="item.name"
          @click="addItem(item.type)"
          class="ma-2"
          small
        >
          {{ item.name }}
        </v-chip>
          <v-menu
            bottom
            left
          >
            <template v-slot:activator="{ on, attrs }">
              <v-btn
                icon
                v-bind="attrs"
                v-on="on"
              >
                <v-icon>fas fa-plus</v-icon>
              </v-btn>
            </template>

            <v-list>
              <v-list-item
                v-for="i in integrations"
                :key="i.type"
                @click="addIntegration(i)"
              >
                <v-list-item-title>Add {{ i.name }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import draggable from 'vuedraggable'
export default {
  components: { draggable },
  props: {
    value: {
      type: Array,
      default: () => { return [] }
    },
    addIntegrations: {
      type: Boolean,
      default: false
    }
  },
  data: vm => ({
    form: [],
    search: '',
    drag: false,
    items: [
      { type: 'input', name: vm.$t('form.small') },
      { type: 'text', name: vm.$t('form.long') },
      { type: 'check', name: vm.$t('form.check') },
      { type: 'combo', name: vm.$t('form.combo') },
      { type: 'upload', name: vm.$t('form.upload') }
    ],
    dragOptions: {
      animation: 200,
      group: 'description',
      disabled: false,
      ghostClass: 'ghost'
    },
    integrations: [
      { type: 'asana', name: 'Asana' }
    ]
  }),
  mounted () {
    // checking if integrations are enabled
  },
  watch: {
    value: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    }
  },
  methods: {
    addItem (name) {
      if (name === 'combo') {
        this.value.push({ type: 'select', text: '', options: [{ name: '', id: this.getRandomString() }], id: this.getRandomString() })
      } else if (name === 'check') {
        this.value.push({ type: 'check', text: '', items: [{ name: '', id: this.getRandomString() }], id: this.getRandomString() })
      } else {
        this.value.push({ type: name, text: '', id: this.getRandomString() })
      }
    },
    addIntegration (i) {
      if (i.type === 'asana') {
        // pass
      }
    },
    getRandomString () {
      // from https://stackoverflow.com/a/6860916
      return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1)
    },
    addSubItem (list) {
      list.push({ name: '', id: this.getRandomString() })
    }
  }
}
</script>

<style>
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
  width: 100%;
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
</style>
