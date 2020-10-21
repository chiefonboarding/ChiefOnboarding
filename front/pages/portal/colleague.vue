<template>
  <v-container>
    <LoadingIcon :color="$store.state.baseInfo.org.base_color" :is-loading="loading" />

    <v-container v-if="!loading && intros.length > 0" grid-list-xl fluid>
      <h1 style="margin-bottom: 20px;">
        {{ $t('newHirePortal.somePeople') }}
      </h1>
      <v-row wrap>
        <v-col
          v-for="i in intros"
          :key="i.id"
          sm="3"
        >
          <IntroductionItem :title="i.name" :user="i.intro_person" />
        </v-col>
      </v-row>
    </v-container>

    <v-container v-if="!loading && colleagues.length" grid-list-xl fluid>
      <v-row>
        <v-col cols="12">
          <h2 style="margin-bottom: 10px;">
            {{ $t('newHirePortal.hereAre') }}
          </h2>
        </v-col>
      </v-row>
      <v-row>
        <v-card outlined class="mx-3" style="width: 100%">
          <v-container grid-list-xl>
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="searchName"
                  :color="$store.state.baseInfo.org.base_color"
                  @input="updateResults"
                  label="Search by name..."
                />
              </v-col>
              <v-col cols="6">
                <v-autocomplete
                  v-model="searchDepartment"
                  :items="departments"
                  :color="$store.state.baseInfo.org.base_color"
                  @input="updateResults"
                  label="Select department"
                  deletable-chips
                  multiple
                />
              </v-col>
            </v-row>
          </v-container>
        </v-card>
      </v-row>
      <v-row
        v-for="(colleagues, value) in results"
        :key="value"
        wrap
      >
        <v-col cols="12">
          <h2>{{ value }}</h2>
        </v-col>
        <v-col
          v-for="colleague in colleagues"
          :key="colleague.id"
          sm="3"
        >
          <ColleagueItem :colleague="colleague" />
        </v-col>
      </v-row>
    </v-container>
  </v-container>
</template>

<script>
import Mustache from 'mustache'
import IntroductionItem from '@/components/portal/IntroductionItem'
import ColleagueItem from '@/components/portal/ColleagueItem'
export default {
  name: 'Colleagues',
  layout: 'newhire',
  components: { IntroductionItem, ColleagueItem },
  filters: {
    addHTTPS (string) {
      return (!string.includes('http')) ? 'https://' + string : string
    }
  },
  data: () => ({
    colleagues: [],
    intros: [],
    results: [],
    loading: true,
    searchDepartment: '',
    searchName: ''
  }),
  mounted () {
    this.loading = true
    this.$newhirepart.getEmployees().then((data) => {
      this.colleagues = data
      this.departments = [...new Set(data.map(a => a.department))]
      this.updateResults()
      this.$newhirepart.getIntroductions().then((data) => {
        this.intros = data
        const introId = this.intros.map(a => a.intro_person.id)
        this.colleagues = this.colleagues.filter(a => !introId.includes(a.id))
      }).finally(() => {
        this.loading = false
      })
    })
  },
  methods: {
    groupBy (xs, f) {
      return xs.reduce((r, v, i, a, k = f(v)) => ((r[k] || (r[k] = [])).push(v), r), {}) // eslint-disable-line
    },
    mustaching (content) {
      if (content === null) { return }
      return Mustache.render(content, this.$store.state.baseInfo)
    },
    updateResults () {
      const searchDepartments = (this.searchDepartment.length === 0) ? this.departments : this.searchDepartment
      this.results = this.groupBy(this.colleagues.filter(a => searchDepartments.includes(a.department) && a.full_name.includes(this.searchName)), (c) => { return c.department })
    }
  }
}
</script>
