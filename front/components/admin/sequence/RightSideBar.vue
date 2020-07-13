<template>
  <v-navigation-drawer
    v-model="$store.state.rightSideBar"
    :mobile-breakpoint="400"
    clipped
    right
    fixed
    app
  >
    <v-list v-if="mainMenu" dense class="pt-0">
      <v-subheader>
        {{ $t('sideBar.blocks') }}
      </v-subheader>
      <v-list-item
        @click="showBlockModal = true"
        class="menu-side"
      >
        <drag :transfer-data="{type: 'block'}" :draggable="false" style="display: flex; width: 100%;" class="dragging">
          <v-list-item-action>
            <v-icon>fas fa-code-branch</v-icon>
          </v-list-item-action>

          <v-list-item-content>
            <v-list-item-title> {{ $t('sideBar.addBlock') }}</v-list-item-title>
          </v-list-item-content>
        </drag>
      </v-list-item>
      <v-subheader>
        {{ $t('sideBar.items') }}
      </v-subheader>
      <v-list-item
        v-for="item in sideBarItems"
        :key="item.title"
        @click="changeMenu(item)"
        class="menu-side"
      >
        <drag :transfer-data="{item: item, type: item.type}" :draggable="!item.arrow" style="display: flex; width: 100%;" class="dragging">
          <v-list-item-action style="margin-top: 11px;">
            <v-icon>{{ item.icon }}</v-icon>
          </v-list-item-action>

          <v-list-item-content>
            <v-list-item-title>
              {{ item.title }} <div v-if="item.arrow" style="float: right;margin-top:-2px">
                <v-icon small>
                  fas fa-arrow-right
                </v-icon>
              </div>
            </v-list-item-title>
          </v-list-item-content>
        </drag>
      </v-list-item>
    </v-list>

    <v-list v-else dense class="pt-0 thispart">
      <v-list-item
        @click="backToMain"
      >
        <v-list-item-action>
          <v-icon small>
            fas fa-arrow-left
          </v-icon>
        </v-list-item-action>
        <v-list-item-content>
          <v-list-item-title>{{ $t('sideBar.goBack') }} </v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <v-list-item style="height: 49px;">
        <v-list-item-content style="height: 49px;">
          <v-text-field
            v-model="search"
            :label="$t('admin.search')"
            style="margin: 10px 0px; width: 100%; margin-top: -10px;"
          />
        </v-list-item-content>
      </v-list-item>
      <v-divider />
      <v-list-item
        class="menu-side"
      >
        <drag :transfer-data="{item: {id: -1}, type: type}" class="dragging">
          <v-row>
            <v-col sm="3">
              <v-list-item-action style="margin-top: 7px; height: 10px">
                <i class="fas fa-plus" style="font-size: 16px;margin-bottom: 8px;" />
              </v-list-item-action>
            </v-col>
            <v-col>
              <v-list-item-content>
                <v-list-item-title>{{ $t('sideBar.newItem') }}</v-list-item-title>
              </v-list-item-content>
            </v-col>
          </v-row>
        </drag>
      </v-list-item>
      <v-list-item
        v-for="item in makeSearch(items)"
        :key="item.id"
        class="menu-side"
      >
        <v-tooltip top style="width: 100%;">
          <template v-slot:activator="{ on }">
            <drag :transfer-data="{item: item, type: type}" v-on="on" class="dragging">
              <v-list-item-content>
                <v-list-item-title>{{ item.name }}</v-list-item-title>
              </v-list-item-content>
            </drag>
          </template>
          <span>{{ getTags(item) }}</span>
        </v-tooltip>
      </v-list-item>
    </v-list>
    <v-dialog
      v-model="showBlockModal"
      :persistent="true"
      max-width="800"
      scrollable
    >
      <v-card>
        <v-card-title class="headline">
          {{ $t('sideBar.addNewBlock') }}
        </v-card-title>
        <v-card-text>
          <v-col sm="12" class="mb-3">
            <p>{{ $t('sideBar.modalQuestion') }}</p>
            <v-btn-toggle v-model="condition" :mandatory="true">
              <v-btn :value="1" text>
                {{ $t('sideBar.basedOnToDo') }}
              </v-btn>
              <v-btn :value="2" text>
                {{ $t('sideBar.beforeStarting') }}
              </v-btn>
              <v-btn :value="0" text>
                {{ $t('sideBar.afterStarting') }}
              </v-btn>
            </v-btn-toggle>
          </v-col>
          <v-col v-if="condition !== 1" sm="12" class="mb-3">
            <p>
              <span v-if="condition === 0">{{ $t('sideBar.createBlockFor') }}</span><span v-else>{{ $t('sideBar.createBlock') }}</span>
              <v-text-field
                v-model="amountOfDays"
                required
                type="number"
                style="display:inline-block; margin: 0px 5px; width: 50px;"
              />
              <span v-if="condition === 2">{{ $t('sideBar.daysBefore') }}</span><span v-else>{{ $t('sideBar.workingDays') }}</span>
            </p>
          </v-col>
          <v-col v-else sm="12" class="mb-3">
            <div v-if="condition === 1">
              <v-combobox
                v-model="conditions"
                :items="$store.state.todos.all"
                :label="$t('sideBar.waitFor')"
                item-text="name"
                multiple
                chips
              />
            </div>
          </v-col>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            @click="showBlockModal = false; resetBlock()"
            text
          >
            {{ $t('buttons.cancel') }}
          </v-btn>
          <v-btn
            @click="addBlock(); showBlockModal = false; resetBlock()"
          >
            {{ $t('buttons.add') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-navigation-drawer>
</template>

<script>
export default {
  name: 'RightSideBar',
  data: vm => ({
    sideBarItems: [
      { id: 1, icon: 'fas fa-check', title: vm.$t('sideBar.toDo'), arrow: true },
      { id: 2, icon: 'far fa-folder', title: vm.$t('sideBar.resource'), arrow: true },
      { id: 3, icon: 'far fa-arrow-alt-circle-right', title: vm.$t('sideBar.badge'), arrow: true },
      { id: 4, icon: 'fa fa-tasks', title: vm.$t('sideBar.admin'), arrow: false, type: 'admin_tasks' },
      { id: 5, icon: 'far fa-comment', title: vm.$t('sideBar.text'), arrow: false, type: 2 },
      { id: 6, icon: 'far fa-envelope', title: vm.$t('sideBar.email'), arrow: false, type: 0 },
      { id: 7, icon: 'fab fa-slack-hash', title: vm.$t('sideBar.slack'), arrow: false, type: 1 }
    ],
    mainMenu: true,
    showBlockModal: false,
    amountOfDays: 1,
    items: [],
    conditions: [],
    type: '',
    condition: 1,
    search: ''
  }),
  methods: {
    changeMenu (item) {
      if (item.id === 1) {
        this.items = this.$store.state.todos.all
        this.type = 'to_do'
      } else if (item.id === 2) {
        this.items = this.$store.state.resources.all
        this.type = 'resources'
      } else if (item.id === 3) {
        this.items = this.$store.state.badges.all
        this.type = 'badges'
      }
      if (item.id === 1 || item.id === 2 || item.id === 3) {
        this.mainMenu = false
      }
    },
    backToMain (item) {
      this.mainMenu = true
      this.search = ''
    },
    addBlock () {
      const toDoItems = []
      if (this.condition === 1) {
        this.conditions.forEach((one) => {
          toDoItems.push(one)
        })
      }
      this.$store.commit('sequences/addTimeLineItem', {
        to_do: [],
        resources: [],
        appointments: [],
        badges: [],
        admin_tasks: [],
        external_messages: [],
        days: this.amountOfDays,
        condition_to_do: toDoItems,
        condition_type: this.condition
      })
    },
    resetBlock () {
      this.condition = 1
      this.conditions = []
      this.amountOfDays = 1
    },
    getTags (item) {
      let data = ''
      item.tags.forEach((a) => { data += a + ', ' })
      if (data.length > 0) {
        return data.substring(0, data.length - 2)
      } else {
        return 'No tags'
      }
    },
    makeSearch (items) {
      const newItems = []
      items.forEach((a) => {
        if (a.name.toLowerCase().includes(this.search.toLowerCase())) { newItems.push(a) }
      })
      return newItems
    }
  }
}
</script>

<style>
  .menu-side {
    cursor:pointer;
  }
  .dragging {
    width: 100%;
  }
</style>
