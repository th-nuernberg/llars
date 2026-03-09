<template>
  <div class="db-agent-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <LIcon size="32" color="primary">llars:train</LIcon>
        <div class="header-text">
          <h1 class="title">{{ $t('dbAgent.title') }}</h1>
          <p class="subtitle">{{ $t('dbAgent.subtitle') }}</p>
        </div>
      </div>
      <div class="header-actions">
        <LTag :variant="status.running ? 'success' : 'default'" size="sm">
          <LIcon start size="14">{{ status.running ? 'mdi-pulse' : 'mdi-pause' }}</LIcon>
          {{ status.running ? $t('dbAgent.status.active') : $t('dbAgent.status.inactive') }}
        </LTag>
        <LBtn
          v-if="!status.running"
          variant="primary"
          size="small"
          @click="startScheduler"
          :loading="actionLoading"
        >
          {{ $t('dbAgent.actions.startAgent') }}
        </LBtn>
        <LBtn
          v-else
          variant="cancel"
          size="small"
          @click="stopScheduler"
          :loading="actionLoading"
        >
          {{ $t('dbAgent.actions.stopAgent') }}
        </LBtn>
        <LBtn
          variant="accent"
          size="small"
          @click="triggerScan"
          :loading="status.is_scanning"
          :disabled="status.is_scanning"
        >
          <LIcon start size="16">llars:refresh</LIcon>
          {{ $t('dbAgent.actions.scanNow') }}
        </LBtn>
        <LBtn
          variant="danger"
          size="small"
          @click="deleteAllData"
          :loading="actionLoading"
        >
          <LIcon start size="16">mdi-delete</LIcon>
          {{ $t('dbAgent.actions.deleteData') }}
        </LBtn>
      </div>
    </div>

    <!-- Search Bar (always visible, above tabs) -->
    <div class="search-bar mt-3">
      <!-- Station row -->
      <div class="search-fields search-stations">
        <v-combobox
          v-model="searchStationFrom"
          :items="stationSuggestions"
          :label="$t('dbAgent.search.stationFrom')"
          density="compact"
          variant="outlined"
          hide-details
          class="station-field"
          prepend-inner-icon="llars:train-outbound"
        />
        <LBtn variant="text" size="small" @click="swapStations" class="swap-btn">
          <LIcon size="18">mdi-swap-horizontal</LIcon>
        </LBtn>
        <v-combobox
          v-model="searchStationTo"
          :items="stationSuggestions"
          :label="$t('dbAgent.search.stationTo')"
          density="compact"
          variant="outlined"
          hide-details
          class="station-field"
          prepend-inner-icon="llars:train-return"
        />
      </div>
      <!-- Date row -->
      <div class="search-fields mt-2">
        <div class="search-leg">
          <LIcon size="16" color="primary">llars:train-outbound</LIcon>
          <span class="search-leg-label">{{ $t('dbAgent.search.outbound') }}</span>
          <v-text-field
            v-model="searchDateFrom"
            type="date"
            :label="$t('dbAgent.search.dateFrom')"
            density="compact"
            variant="outlined"
            hide-details
            class="date-field"
          />
        </div>
        <div class="search-leg">
          <LIcon size="16">llars:train-return</LIcon>
          <span class="search-leg-label">{{ $t('dbAgent.search.returnTrip') }}</span>
          <v-text-field
            v-model="searchDateTo"
            type="date"
            :label="$t('dbAgent.search.dateTo')"
            density="compact"
            variant="outlined"
            hide-details
            class="date-field"
          />
        </div>
        <v-select
          v-model="searchFlexibility"
          :items="flexOptions"
          item-title="label"
          item-value="value"
          :label="$t('dbAgent.search.flexibility')"
          density="compact"
          variant="outlined"
          hide-details
          class="flex-field"
        />
        <LBtn variant="primary" @click="searchTrip" :loading="searchLoading" :disabled="false">
          <LIcon start size="16">llars:search</LIcon>
          {{ searchLoading ? $t('dbAgent.search.newSearch') : $t('dbAgent.search.go') }}
        </LBtn>
      </div>
    </div>

    <LTabs v-model="activeTab" :tabs="tabs" class="mt-3" />

    <!-- ==================== TAB: REISE SUCHEN ==================== -->
    <div v-show="activeTab === 'search'" class="tab-content">
      <!-- Split Search Results: Outbound | Return (shown FIRST, above overview) -->
      <div v-if="outboundResults.length || returnResults.length || searchLoading" class="trip-split-panels">
        <!-- LEFT: Outbound (Dortmund → Nürnberg) -->
        <div class="trip-panel">
          <div class="trip-panel-header trip-panel-header--outbound">
            <LIcon size="18" color="primary">llars:train-outbound</LIcon>
            <span>{{ $t('dbAgent.search.outbound') }}</span>
            <LTag variant="primary" size="sm">{{ stationShort(searchStationFrom) }} → {{ stationShort(searchStationTo) }}</LTag>
            <span class="trip-panel-date">{{ formatDate(searchDateFrom) }}</span>
            <LTag v-if="searchLoading" variant="default" size="sm" class="ml-auto">
              <LIcon size="12">mdi-loading mdi-spin</LIcon> {{ outboundResults.length }}…
            </LTag>
          </div>
          <div v-if="outboundResults.length" class="trip-panel-list">
            <div
              v-for="(s, idx) in outboundResults"
              :key="'out-' + idx"
              class="suggestion-card suggestion-card--compact"
              :class="{ 'suggestion-card--selected': selectedOutbound === idx, 'suggestion-card--night': s.is_night }"
              @click="selectedOutbound = idx"
            >
              <div class="suggestion-number">#{{ idx + 1 }}</div>
              <span v-if="s.is_night" class="night-badge"><LIcon size="14">mdi-weather-night</LIcon></span>
              <div class="suggestion-main">
                <div class="suggestion-details">
                  <span class="suggestion-date"><LIcon size="14">llars:calendar</LIcon> {{ formatDate(s.travel_date) }}</span>
                  <span class="suggestion-time"><LIcon size="14">llars:clock</LIcon> {{ formatTime(s.departure) }} → {{ formatTime(s.arrival) }}</span>
                  <span class="suggestion-duration">{{ s.duration_minutes }} min</span>
                  <LTag :variant="s.is_direct ? 'success' : 'default'" size="sm">{{ s.is_direct ? 'Direkt' : `${s.transfers} Umst.` }}</LTag>
                </div>
                <div class="suggestion-trains">{{ s.train_types }}</div>
              </div>
              <div class="suggestion-price-col">
                <div class="suggestion-price" :class="priceClass(s.price_eur)">{{ s.price_eur.toFixed(2) }}€</div>
                <a :href="buildBahnLink(s)" target="_blank" rel="noopener" class="bahn-link" @click.stop :title="$t('dbAgent.search.bookOnBahn')">
                  <LIcon size="12">mdi-open-in-new</LIcon> bahn.de
                </a>
              </div>
            </div>
          </div>
          <LLoading v-else-if="searchLoading" :text="$t('dbAgent.loading')" />
          <div v-else class="empty-state-small">
            <p>{{ $t('dbAgent.stats.noData') }}</p>
          </div>
        </div>

        <!-- RIGHT: Return (Nürnberg → Dortmund) -->
        <div class="trip-panel">
          <div class="trip-panel-header trip-panel-header--return">
            <LIcon size="18">llars:train-return</LIcon>
            <span>{{ $t('dbAgent.search.returnTrip') }}</span>
            <LTag variant="default" size="sm">{{ stationShort(searchStationTo) }} → {{ stationShort(searchStationFrom) }}</LTag>
            <span class="trip-panel-date">{{ formatDate(searchDateTo) }}</span>
            <LTag v-if="searchLoading" variant="default" size="sm" class="ml-auto">
              <LIcon size="12">mdi-loading mdi-spin</LIcon> {{ returnResults.length }}…
            </LTag>
          </div>
          <div v-if="returnResults.length" class="trip-panel-list">
            <div
              v-for="(s, idx) in returnResults"
              :key="'ret-' + idx"
              class="suggestion-card suggestion-card--compact"
              :class="{ 'suggestion-card--selected': selectedReturn === idx, 'suggestion-card--night': s.is_night }"
              @click="selectedReturn = idx"
            >
              <div class="suggestion-number">#{{ idx + 1 }}</div>
              <span v-if="s.is_night" class="night-badge"><LIcon size="14">mdi-weather-night</LIcon></span>
              <div class="suggestion-main">
                <div class="suggestion-details">
                  <span class="suggestion-date"><LIcon size="14">llars:calendar</LIcon> {{ formatDate(s.travel_date) }}</span>
                  <span class="suggestion-time"><LIcon size="14">llars:clock</LIcon> {{ formatTime(s.departure) }} → {{ formatTime(s.arrival) }}</span>
                  <span class="suggestion-duration">{{ s.duration_minutes }} min</span>
                  <LTag :variant="s.is_direct ? 'success' : 'default'" size="sm">{{ s.is_direct ? 'Direkt' : `${s.transfers} Umst.` }}</LTag>
                </div>
                <div class="suggestion-trains">{{ s.train_types }}</div>
              </div>
              <div class="suggestion-price-col">
                <div class="suggestion-price" :class="priceClass(s.price_eur)">{{ s.price_eur.toFixed(2) }}€</div>
                <a :href="buildBahnLink(s)" target="_blank" rel="noopener" class="bahn-link" @click.stop :title="$t('dbAgent.search.bookOnBahn')">
                  <LIcon size="12">mdi-open-in-new</LIcon> bahn.de
                </a>
              </div>
            </div>
          </div>
          <LLoading v-else-if="searchLoading" :text="$t('dbAgent.loading')" />
          <div v-else class="empty-state-small">
            <p>{{ $t('dbAgent.stats.noData') }}</p>
          </div>
        </div>
      </div>

      <!-- Total Price Bar -->
      <div v-if="selectedOutboundJourney || selectedReturnJourney" class="trip-total-bar">
        <div class="trip-total-selections">
          <div v-if="selectedOutboundJourney" class="trip-total-leg">
            <LTag variant="primary" size="sm">{{ stationShort(searchStationFrom) }} → {{ stationShort(searchStationTo) }}</LTag>
            <span>{{ formatDate(selectedOutboundJourney.travel_date) }}</span>
            <span>{{ formatTime(selectedOutboundJourney.departure) }} → {{ formatTime(selectedOutboundJourney.arrival) }}</span>
            <strong :class="priceClass(selectedOutboundJourney.price_eur)">{{ selectedOutboundJourney.price_eur.toFixed(2) }}€</strong>
          </div>
          <div v-else class="trip-total-leg trip-total-leg--empty">
            <LTag variant="primary" size="sm">{{ stationShort(searchStationFrom) }} → {{ stationShort(searchStationTo) }}</LTag>
            <span class="text-muted">{{ $t('dbAgent.search.selectOutbound') }}</span>
          </div>
          <LIcon size="18">mdi-plus</LIcon>
          <div v-if="selectedReturnJourney" class="trip-total-leg">
            <LTag variant="default" size="sm">{{ stationShort(searchStationTo) }} → {{ stationShort(searchStationFrom) }}</LTag>
            <span>{{ formatDate(selectedReturnJourney.travel_date) }}</span>
            <span>{{ formatTime(selectedReturnJourney.departure) }} → {{ formatTime(selectedReturnJourney.arrival) }}</span>
            <strong :class="priceClass(selectedReturnJourney.price_eur)">{{ selectedReturnJourney.price_eur.toFixed(2) }}€</strong>
          </div>
          <div v-else class="trip-total-leg trip-total-leg--empty">
            <LTag variant="default" size="sm">{{ stationShort(searchStationTo) }} → {{ stationShort(searchStationFrom) }}</LTag>
            <span class="text-muted">{{ $t('dbAgent.search.selectReturn') }}</span>
          </div>
        </div>
        <div class="trip-total-price" v-if="totalPrice != null">
          <span class="trip-total-label">{{ $t('dbAgent.search.totalPrice') }}</span>
          <span class="trip-total-amount" :class="priceClass(totalPrice)">{{ totalPrice.toFixed(2) }}€</span>
          <a v-if="selectedOutboundJourney" :href="buildBahnLink(selectedOutboundJourney)" target="_blank" rel="noopener" class="bahn-link-lg">
            <LIcon size="16">mdi-open-in-new</LIcon> {{ $t('dbAgent.search.bookOnBahn') }}
          </a>
        </div>
      </div>

      <!-- Follow-Up Chat -->
      <div class="followup-section" v-if="outboundResults.length || returnResults.length">
        <div class="section-header">
          <LIcon size="20" color="accent">llars:chat</LIcon>
          <h2>{{ $t('dbAgent.followup.title') }}</h2>
        </div>
        <div class="followup-messages" ref="messagesContainer">
          <div v-for="(msg, idx) in chatMessages" :key="idx" class="chat-message" :class="`chat-message--${msg.role}`">
            <div class="chat-avatar">
              <LIcon size="20" :color="msg.role === 'assistant' ? 'accent' : 'primary'">
                {{ msg.role === 'assistant' ? 'llars:robot' : 'mdi-account' }}
              </LIcon>
            </div>
            <div class="chat-bubble" v-html="renderMarkdown(msg.content)"></div>
          </div>
          <div v-if="chatLoading" class="chat-message chat-message--assistant">
            <div class="chat-avatar"><LIcon size="20" color="accent">llars:robot</LIcon></div>
            <div class="chat-bubble"><LLoading text="" /></div>
          </div>
        </div>
        <div class="followup-input">
          <v-text-field
            v-model="chatInput"
            :placeholder="$t('dbAgent.followup.placeholder')"
            density="compact"
            variant="outlined"
            hide-details
            @keyup.enter="sendFollowup"
          />
          <LBtn variant="primary" @click="sendFollowup" :loading="chatLoading" :disabled="!chatInput.trim()">
            <LIcon size="18">mdi-send</LIcon>
          </LBtn>
        </div>
      </div>

      <!-- Search History -->
      <div v-if="searchHistory.length" class="search-history-section">
        <div class="section-header">
          <LIcon size="20" color="secondary">mdi-history</LIcon>
          <h2>{{ $t('dbAgent.history.title') }}</h2>
        </div>
        <div class="search-history-list">
          <div
            v-for="h in searchHistory"
            :key="h.id"
            class="search-history-card"
            @click="restoreSearch(h)"
          >
            <div class="search-history-main">
              <div class="search-history-route">
                <LTag variant="primary" size="sm">{{ stationShort(h.stationFrom) }} → {{ stationShort(h.stationTo) }}</LTag>
                <span class="search-history-dates">
                  {{ formatDate(h.dateFrom) }} — {{ formatDate(h.dateTo) }}
                </span>
                <LTag v-if="h.flexibility" variant="default" size="sm">±{{ h.flexibility }}d</LTag>
              </div>
              <div class="search-history-stats">
                <span v-if="h.cheapestOut != null" class="search-history-price" :class="priceClass(h.cheapestOut)">
                  {{ $t('dbAgent.search.outbound') }} ab {{ h.cheapestOut.toFixed(2) }}€
                </span>
                <span v-if="h.cheapestRet != null" class="search-history-price" :class="priceClass(h.cheapestRet)">
                  {{ $t('dbAgent.search.returnTrip') }} ab {{ h.cheapestRet.toFixed(2) }}€
                </span>
                <span class="search-history-count">{{ h.outbound.length + h.return.length }} Verbindungen</span>
              </div>
            </div>
            <div class="search-history-actions">
              <span class="search-history-time">{{ h.timestamp }}</span>
              <LIconBtn icon="mdi-close" size="small" @click.stop="removeSearchHistory(h.id)" tooltip="Entfernen" />
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Overview / Top Deals (shown when NO search results and NOT searching) -->
      <div v-if="overviewLoading && !searchLoading && !outboundResults.length" class="overview-loading">
        <LLoading :text="$t('dbAgent.overview.loading')" />
      </div>

      <div v-if="!overviewLoading && !searchLoading && overviewDeals.length && !outboundResults.length && !returnResults.length" class="overview-section">
        <div class="section-header">
          <LIcon size="20" color="success">llars:deal</LIcon>
          <h2>{{ $t('dbAgent.overview.topDeals') }}</h2>
          <LTag v-if="overviewSource === 'live_sample'" variant="info" size="sm">Live</LTag>
          <LTag v-else variant="success" size="sm">{{ $t('dbAgent.overview.fromScans') }}</LTag>
        </div>
        <div class="suggestions-list">
          <div v-for="(s, idx) in overviewDeals" :key="idx" class="suggestion-card" :class="{ 'suggestion-card--night': s.is_night }">
            <div class="suggestion-number">#{{ idx + 1 }}</div>
            <div class="suggestion-main">
              <div class="suggestion-route">
                <LTag :variant="s.direction === 'outbound' ? 'primary' : 'default'" size="sm">
                  {{ s.direction === 'outbound' ? `${stationShort(searchStationFrom)} → ${stationShort(searchStationTo)}` : `${stationShort(searchStationTo)} → ${stationShort(searchStationFrom)}` }}
                </LTag>
                <span v-if="s.is_night" class="night-badge">
                  <LIcon size="14">mdi-weather-night</LIcon>
                </span>
              </div>
              <div class="suggestion-details">
                <span class="suggestion-date"><LIcon size="14">llars:calendar</LIcon> {{ formatDate(s.travel_date) }}</span>
                <span class="suggestion-time"><LIcon size="14">llars:clock</LIcon> {{ formatTime(s.departure) }} → {{ formatTime(s.arrival) }}</span>
                <span class="suggestion-duration">{{ s.duration_minutes }} min</span>
                <LTag :variant="s.is_direct ? 'success' : 'default'" size="sm">{{ s.is_direct ? 'Direkt' : `${s.transfers} Umst.` }}</LTag>
              </div>
              <div class="suggestion-trains">{{ s.train_types }}</div>
            </div>
            <div class="suggestion-price-col">
              <div class="suggestion-price" :class="priceClass(s.price_eur)">{{ s.price_eur.toFixed(2) }}€</div>
              <a :href="buildBahnLink(s)" target="_blank" rel="noopener" class="bahn-link" :title="$t('dbAgent.search.bookOnBahn')">
                <LIcon size="14">mdi-open-in-new</LIcon> bahn.de
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== TAB: TOP DEALS ==================== -->
    <div v-show="activeTab === 'deals'" class="tab-content">
      <div class="section-header">
        <LIcon size="20" color="success">llars:deal</LIcon>
        <h2>{{ $t('dbAgent.deals.title') }}</h2>
        <LBtn variant="text" size="small" @click="fetchDeals" :loading="dealsLoading">
          <LIcon size="16">llars:refresh</LIcon>
        </LBtn>
      </div>

      <LLoading v-if="dealsLoading" :text="$t('dbAgent.loading')" />
      <div v-else-if="deals.length" class="suggestions-list">
        <div
          v-for="(s, idx) in deals"
          :key="s.id"
          class="suggestion-card"
          :class="{ 'suggestion-card--night': s.is_night }"
        >
          <div class="suggestion-number">#{{ idx + 1 }}</div>
          <div class="suggestion-main">
            <div class="suggestion-route">
              <LTag :variant="s.direction === 'outbound' ? 'primary' : 'default'" size="sm">
                {{ s.direction === 'outbound' ? `${stationShort(searchStationFrom)} → ${stationShort(searchStationTo)}` : `${stationShort(searchStationTo)} → ${stationShort(searchStationFrom)}` }}
              </LTag>
              <span v-if="s.is_night" class="night-badge">
                <LIcon size="14">mdi-weather-night</LIcon>
              </span>
            </div>
            <div class="suggestion-details">
              <span class="suggestion-date">
                <LIcon size="14">llars:calendar</LIcon>
                {{ formatDate(s.travel_date) }}
              </span>
              <span class="suggestion-time">
                <LIcon size="14">llars:clock</LIcon>
                {{ formatTime(s.departure) }} → {{ formatTime(s.arrival) }}
              </span>
              <LTag :variant="s.is_direct ? 'success' : 'default'" size="sm">
                {{ s.is_direct ? 'Direkt' : `${s.transfers} Umst.` }}
              </LTag>
            </div>
            <div class="suggestion-trains">{{ s.train_types }}</div>
          </div>
          <div class="suggestion-price-col">
              <div class="suggestion-price" :class="priceClass(s.price_eur)">
                {{ s.price_eur.toFixed(2) }}€
              </div>
              <a :href="buildBahnLink(s)" target="_blank" rel="noopener" class="bahn-link" :title="$t('dbAgent.search.bookOnBahn')">
                <LIcon size="14">mdi-open-in-new</LIcon>
                bahn.de
              </a>
            </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <LIcon size="48" color="grey">llars:train</LIcon>
        <p>{{ $t('dbAgent.stats.noData') }}</p>
      </div>
    </div>

    <!-- ==================== TAB: KALENDER ==================== -->
    <div v-show="activeTab === 'calendar'" class="tab-content">
      <div class="section-header">
        <LIcon size="20" color="primary">llars:calendar</LIcon>
        <h2>{{ $t('dbAgent.calendar.title') }}</h2>

        <!-- View mode toggle -->
        <v-btn-toggle v-model="calendarView" mandatory density="compact" variant="outlined" class="ml-2">
          <v-btn value="year" size="small">{{ $t('dbAgent.calendar.viewYear') }}</v-btn>
          <v-btn value="month" size="small">{{ $t('dbAgent.calendar.viewMonth') }}</v-btn>
          <v-btn value="day" size="small">{{ $t('dbAgent.calendar.viewDay') }}</v-btn>
        </v-btn-toggle>

        <!-- Month navigation (month + day view) -->
        <div v-if="calendarView !== 'year'" class="calendar-controls">
          <LBtn variant="text" size="small" @click="calendarView === 'day' ? navigateDayView(-1) : calendarMonthOffset--">
            <LIcon size="18">mdi-chevron-left</LIcon>
          </LBtn>
          <span class="calendar-month-label">
            {{ calendarView === 'day' ? formatDateLong(selectedDayDate) : calendarMonthLabel }}
          </span>
          <LBtn variant="text" size="small" @click="calendarView === 'day' ? navigateDayView(1) : calendarMonthOffset++">
            <LIcon size="18">mdi-chevron-right</LIcon>
          </LBtn>
        </div>

        <v-btn-toggle v-model="calendarDirection" mandatory density="compact" variant="outlined" class="ml-auto">
          <v-btn value="outbound" size="small">{{ stationShort(searchStationFrom) }} → {{ stationShort(searchStationTo) }}</v-btn>
          <v-btn value="return" size="small">{{ stationShort(searchStationTo) }} → {{ stationShort(searchStationFrom) }}</v-btn>
        </v-btn-toggle>
      </div>

      <LLoading v-if="calendarLoading" :text="$t('dbAgent.loading')" />

      <!-- ===== YEAR VIEW ===== -->
      <template v-else-if="calendarView === 'year'">
        <div class="year-grid">
          <div v-for="month in yearMonths" :key="month.key" class="year-month-card" @click="goToMonth(month.offset)">
            <div class="year-month-name">{{ month.label }}</div>
            <div class="year-month-mini-grid">
              <v-tooltip
                v-for="(cell, idx) in month.cells"
                :key="idx"
                :disabled="!cell.date"
                location="top"
                content-class="year-cell-tooltip"
              >
                <template #activator="{ props: tp }">
                  <div
                    v-bind="tp"
                    class="year-mini-cell"
                    :class="{
                      'year-mini-cell--empty': !cell.date,
                      [priceClass(cell.cheapest)]: cell.date && cell.cheapest != null,
                    }"
                    @click.stop="cell.date && goToDay(cell.date)"
                  ></div>
                </template>
                <div v-if="cell.date" class="year-tooltip-content">
                  <div class="year-tooltip-date">{{ formatDateLong(cell.date) }}</div>
                  <template v-if="cell.cheapest != null">
                    <div class="year-tooltip-row">
                      <span>{{ $t('dbAgent.calendar.cheapestShort') }}</span>
                      <strong :class="priceClass(cell.cheapest)">{{ cell.cheapest }}€</strong>
                    </div>
                    <div class="year-tooltip-row">
                      <span>Ø</span>
                      <span>{{ cell.average }}€</span>
                    </div>
                    <div v-if="cell.std_dev > 0" class="year-tooltip-row">
                      <span>σ</span>
                      <span>{{ cell.std_dev }}€</span>
                    </div>
                    <div class="year-tooltip-row">
                      <span>{{ $t('dbAgent.calendar.connections') }}</span>
                      <span>{{ cell.count }}</span>
                    </div>
                  </template>
                  <div v-else class="text-muted">{{ $t('dbAgent.stats.noData') }}</div>
                </div>
              </v-tooltip>
            </div>
            <div v-if="month.cheapest != null" class="year-month-summary">
              <span :class="priceClass(month.cheapest)">{{ $t('dbAgent.calendar.cheapestShort') }} {{ month.cheapest }}€</span>
            </div>
            <div v-else class="year-month-summary text-muted">—</div>
          </div>
        </div>
      </template>

      <!-- ===== MONTH VIEW ===== -->
      <template v-else-if="calendarView === 'month'">
        <div class="real-calendar">
          <div class="cal-header">
            <div v-for="wd in weekdayHeaders" :key="wd" class="cal-header-cell">{{ wd }}</div>
          </div>
          <div class="cal-body">
            <div
              v-for="(cell, idx) in calendarCells"
              :key="idx"
              class="cal-cell"
              :class="{
                'cal-cell--empty': !cell.date,
                'cal-cell--today': cell.isToday,
                'cal-cell--past': cell.isPast,
                [priceClass(cell.cheapest)]: cell.date && cell.cheapest != null,
              }"
              @click="cell.date && openDayView(cell.date)"
              @mouseenter="hoveredCalDay = cell.date"
              @mouseleave="hoveredCalDay = null"
            >
              <template v-if="cell.date">
                  <span class="cal-day-num">{{ cell.dayNum }}</span>
                  <span v-if="cell.cheapest != null" class="cal-day-price" :class="priceClass(cell.cheapest)">
                    {{ cell.cheapest }}€
                  </span>
                  <span v-if="cell.std_dev > 0" class="cal-day-sigma" :class="{ 'cal-day-sigma--high': cell.std_dev > 15 }">
                    ±{{ cell.std_dev }}
                  </span>
                </template>
              </div>
            </div>
          </div>

          <!-- Trip Recommendations -->
          <div v-if="calendarTrips.length" class="trip-recommendations">
            <div class="section-header mt-4">
              <LIcon size="18" color="success">llars:deal</LIcon>
              <h3>{{ $t('dbAgent.calendar.tripSuggestions') }}</h3>
            </div>
            <div class="trip-strips">
              <div
                v-for="(trip, idx) in calendarTrips"
                :key="idx"
                class="trip-strip-card"
                :class="priceClass(trip.totalPrice)"
                @mouseenter="hoveredTrip = trip"
                @mouseleave="hoveredTrip = null"
              >
                <div class="trip-strip-rank">#{{ idx + 1 }}</div>
                <div class="trip-strip-dates">
                  <span class="trip-strip-range">{{ formatDate(trip.outDate) }} → {{ formatDate(trip.retDate) }}</span>
                  <span class="trip-strip-days">{{ trip.days }} {{ $t('dbAgent.calendar.days') }}</span>
                </div>
                <div class="trip-strip-legs">
                  <div class="trip-strip-leg">
                    <LTag variant="primary" size="sm">DO→N</LTag>
                    <span>{{ formatTime(trip.outDeparture) }}–{{ formatTime(trip.outArrival) }}</span>
                    <span class="trip-strip-leg-price">{{ trip.outPrice.toFixed(2) }}€</span>
                  </div>
                  <div class="trip-strip-leg">
                    <LTag variant="default" size="sm">N→DO</LTag>
                    <span>{{ formatTime(trip.retDeparture) }}–{{ formatTime(trip.retArrival) }}</span>
                    <span class="trip-strip-leg-price">{{ trip.retPrice.toFixed(2) }}€</span>
                  </div>
                </div>
                <div class="trip-strip-total" :class="priceClass(trip.totalPrice)">
                  {{ trip.totalPrice.toFixed(2) }}€
                  <span class="trip-strip-total-label">{{ $t('dbAgent.calendar.roundTrip') }}</span>
                </div>
              </div>
            </div>
          </div>
      </template>

      <!-- ===== DAY VIEW ===== -->
      <template v-else-if="calendarView === 'day'">
        <div v-if="dayViewData.length" class="day-view">
          <div class="day-view-header">
            <LTag :variant="dayViewPriceInfo ? priceClass(dayViewPriceInfo.cheapest) : 'default'" size="sm">
              {{ dayViewPriceInfo ? `${$t('dbAgent.calendar.cheapestShort')} ${dayViewPriceInfo.cheapest}€` : '-' }}
            </LTag>
            <span v-if="dayViewPriceInfo" class="text-muted">
              Ø {{ dayViewPriceInfo.average }}€ · {{ dayViewPriceInfo.count }} {{ $t('dbAgent.calendar.connections') }}
            </span>
          </div>
          <div class="suggestions-list">
            <div
              v-for="(s, idx) in dayViewData"
              :key="idx"
              class="suggestion-card"
              :class="{ 'suggestion-card--night': s.is_night }"
            >
              <div class="suggestion-number">#{{ idx + 1 }}</div>
              <div class="suggestion-main">
                <div class="suggestion-route">
                  <LTag :variant="s.direction === 'outbound' ? 'primary' : 'default'" size="sm">
                    {{ s.direction === 'outbound' ? `${stationShort(searchStationFrom)} → ${stationShort(searchStationTo)}` : `${stationShort(searchStationTo)} → ${stationShort(searchStationFrom)}` }}
                  </LTag>
                  <span v-if="s.is_night" class="night-badge">
                    <LIcon size="14">mdi-weather-night</LIcon>
                  </span>
                </div>
                <div class="suggestion-details">
                  <span class="suggestion-time">
                    <LIcon size="14">llars:clock</LIcon>
                    {{ formatTime(s.departure) }} → {{ formatTime(s.arrival) }}
                  </span>
                  <span class="suggestion-duration">{{ s.duration_minutes }} min</span>
                  <LTag :variant="s.is_direct ? 'success' : 'default'" size="sm">
                    {{ s.is_direct ? 'Direkt' : `${s.transfers} Umst.` }}
                  </LTag>
                </div>
                <div class="suggestion-trains">{{ s.train_types }}</div>
              </div>
              <div class="suggestion-price-col">
                <div class="suggestion-price" :class="priceClass(s.price_eur)">
                  {{ s.price_eur.toFixed(2) }}€
                </div>
                <a :href="buildBahnLink(s)" target="_blank" rel="noopener" class="bahn-link" :title="$t('dbAgent.search.bookOnBahn')">
                  <LIcon size="14">mdi-open-in-new</LIcon>
                  bahn.de
                </a>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <LIcon size="48" color="grey">llars:calendar</LIcon>
          <p>{{ $t('dbAgent.calendar.noDataForDay') }}</p>
        </div>
      </template>

      <!-- Legend (shown for all calendar views) -->
      <div v-if="calendarData.length" class="calendar-legend">
        <span class="legend-item"><span class="legend-dot price-cheap"></span> {{ $t('dbAgent.calendar.legend.cheap') }}</span>
        <span class="legend-item"><span class="legend-dot price-medium"></span> {{ $t('dbAgent.calendar.legend.medium') }}</span>
        <span class="legend-item"><span class="legend-dot price-expensive"></span> {{ $t('dbAgent.calendar.legend.expensive') }}</span>
        <span class="legend-item"><span class="legend-dot price-very-expensive"></span> {{ $t('dbAgent.calendar.legend.veryExpensive') }}</span>
        <span class="legend-item"><span class="legend-dot" style="background: rgba(var(--v-theme-on-surface), 0.2)"></span> {{ $t('dbAgent.calendar.legend.stddev') }}</span>
      </div>
    </div>

    <!-- ==================== TAB: TIMING ==================== -->
    <div v-show="activeTab === 'timing'" class="tab-content">
      <div class="section-header">
        <LIcon size="20" color="primary">mdi-clock-check-outline</LIcon>
        <h2>{{ $t('dbAgent.timing.title') }}</h2>
        <LBtn variant="text" size="small" @click="fetchTiming" :loading="timingLoading">
          <LIcon size="16">llars:refresh</LIcon>
        </LBtn>
      </div>

      <LLoading v-if="timingLoading" :text="$t('dbAgent.loading')" />

      <div v-else-if="timingData.has_data">
        <!-- Tips row -->
        <div v-if="timingTips.length" class="timing-tips">
          <div v-for="tip in timingTips" :key="tip.key" class="timing-tip">
            <LIcon size="16" color="success">mdi-lightbulb-outline</LIcon>
            <span v-if="tip.key === 'leadTime'">{{ $t('dbAgent.timing.tipLeadTime', { bucket: tip.bucket, price: tip.price }) }}</span>
            <span v-else-if="tip.key === 'departure'">{{ $t('dbAgent.timing.tipDeparture', { slot: tip.slot, price: tip.price }) }}</span>
            <span v-else-if="tip.key === 'transfers'">{{ $t('dbAgent.timing.tipTransfers', { label: tip.label, percent: tip.percent }) }}</span>
          </div>
        </div>

        <div class="timing-grid">
          <!-- Departure Time -->
          <div class="timing-card" v-if="timingData.departure_time?.length">
            <div class="timing-card-header">
              <LIcon size="18" color="primary">mdi-clock-outline</LIcon>
              <h3>{{ $t('dbAgent.timing.departureTime') }}</h3>
            </div>
            <p class="timing-hint">{{ $t('dbAgent.timing.departureTimeHint') }}</p>
            <div class="timing-bars">
              <div v-for="slot in timingData.departure_time" :key="slot.slot" class="timing-bar-row">
                <span class="timing-bar-label">{{ slot.slot }}</span>
                <div class="timing-bar-track">
                  <div class="timing-bar-fill" :class="priceClass(slot.avg)" :style="{ width: timingBarWidth(slot.avg, timingData.departure_time) + '%' }"></div>
                </div>
                <span class="timing-bar-value" :class="priceClass(slot.avg)">Ø {{ slot.avg }}€</span>
                <span class="timing-bar-meta">min {{ slot.min }}€ · {{ slot.count }}</span>
              </div>
            </div>
          </div>

          <!-- Booking Lead Time -->
          <div class="timing-card" v-if="timingData.lead_time?.length">
            <div class="timing-card-header">
              <LIcon size="18" color="primary">mdi-calendar-clock</LIcon>
              <h3>{{ $t('dbAgent.timing.leadTime') }}</h3>
            </div>
            <p class="timing-hint">{{ $t('dbAgent.timing.leadTimeHint') }}</p>
            <div class="timing-bars">
              <div v-for="b in timingData.lead_time" :key="b.bucket" class="timing-bar-row">
                <span class="timing-bar-label">{{ b.bucket }}</span>
                <div class="timing-bar-track">
                  <div class="timing-bar-fill" :class="priceClass(b.avg)" :style="{ width: timingBarWidth(b.avg, timingData.lead_time) + '%' }"></div>
                </div>
                <span class="timing-bar-value" :class="priceClass(b.avg)">Ø {{ b.avg }}€</span>
                <span class="timing-bar-meta">min {{ b.min }}€ · {{ b.count }}</span>
              </div>
            </div>
          </div>

          <!-- Transfers Comparison -->
          <div class="timing-card" v-if="timingData.transfers?.length">
            <div class="timing-card-header">
              <LIcon size="18" color="primary">mdi-swap-horizontal</LIcon>
              <h3>{{ $t('dbAgent.timing.transfers') }}</h3>
            </div>
            <p class="timing-hint">{{ $t('dbAgent.timing.transfersHint') }}</p>
            <div class="timing-bars">
              <div v-for="t in timingData.transfers" :key="t.transfers" class="timing-bar-row">
                <span class="timing-bar-label">{{ t.label }}</span>
                <div class="timing-bar-track">
                  <div class="timing-bar-fill" :class="priceClass(t.avg)" :style="{ width: timingBarWidth(t.avg, timingData.transfers) + '%' }"></div>
                </div>
                <span class="timing-bar-value" :class="priceClass(t.avg)">Ø {{ t.avg }}€</span>
                <span class="timing-bar-meta">min {{ t.min }}€ · {{ t.count }}</span>
              </div>
            </div>
          </div>

          <!-- Price Trend -->
          <div class="timing-card" v-if="timingData.price_trend?.length">
            <div class="timing-card-header">
              <LIcon size="18" color="primary">mdi-trending-up</LIcon>
              <h3>{{ $t('dbAgent.timing.priceTrend') }}</h3>
            </div>
            <p class="timing-hint">{{ $t('dbAgent.timing.priceTrendHint') }}</p>
            <div class="timing-bars">
              <div v-for="t in timingData.price_trend" :key="t.bucket" class="timing-bar-row">
                <span class="timing-bar-label">{{ t.bucket }}</span>
                <div class="timing-bar-track">
                  <div class="timing-bar-fill" :class="priceClass(t.avg_cheapest)" :style="{ width: timingBarWidth(t.avg_cheapest, timingData.price_trend.map(x => ({ avg: x.avg_cheapest }))) + '%' }"></div>
                </div>
                <span class="timing-bar-value" :class="priceClass(t.avg_cheapest)">Ø {{ t.avg_cheapest }}€</span>
                <span class="timing-bar-meta">min {{ t.min }}€ · {{ t.dates_with_data }} {{ $t('dbAgent.timing.datesWithData') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <LIcon size="48" color="grey">mdi-clock-check-outline</LIcon>
        <p>{{ $t('dbAgent.timing.noData') }}</p>
      </div>
    </div>

    <!-- ==================== TAB: KI-ANALYSE ==================== -->
    <div v-show="activeTab === 'analysis'" class="tab-content">
      <div class="analysis-cards">
        <!-- Stats -->
        <div class="analysis-card">
          <div class="analysis-card-header">
            <LIcon size="18" color="primary">llars:chart-bar</LIcon>
            <h3>{{ $t('dbAgent.stats.title') }}</h3>
          </div>
          <LLoading v-if="statsLoading" :text="$t('dbAgent.loading')" />
          <div v-else-if="stats.has_data" class="stats-content">
            <div class="stat-row" v-if="stats.outbound">
              <span class="stat-label">{{ $t('dbAgent.stats.outbound') }}</span>
              <span><span class="price-cheap">{{ stats.outbound.min }}€</span> – <span class="price-expensive">{{ stats.outbound.max }}€</span> (Ø {{ stats.outbound.avg }}€)</span>
            </div>
            <div class="stat-row" v-if="stats.return">
              <span class="stat-label">{{ $t('dbAgent.stats.return') }}</span>
              <span><span class="price-cheap">{{ stats.return.min }}€</span> – <span class="price-expensive">{{ stats.return.max }}€</span> (Ø {{ stats.return.avg }}€)</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">{{ $t('dbAgent.stats.totalEntries') }}</span>
              <span>{{ stats.total_entries }}</span>
            </div>
          </div>
          <p v-else class="text-muted">{{ $t('dbAgent.stats.noData') }}</p>
        </div>

        <!-- Weekday -->
        <div class="analysis-card">
          <div class="analysis-card-header">
            <LIcon size="18" color="primary">mdi-calendar-week</LIcon>
            <h3>{{ $t('dbAgent.weekday.title') }}</h3>
          </div>
          <LLoading v-if="weekdayLoading" :text="$t('dbAgent.loading')" />
          <div v-else-if="Object.keys(weekdayData).length" class="weekday-content">
            <div v-for="(data, day) in weekdayData" :key="day" class="weekday-row">
              <span class="weekday-name">{{ day }}</span>
              <div class="weekday-bar" :style="{ width: weekdayBarWidth(data.avg) + '%' }"></div>
              <span class="weekday-price" :class="priceClass(data.avg)">Ø {{ data.avg }}€</span>
              <span class="text-muted">(min {{ data.min }}€)</span>
            </div>
          </div>
          <p v-else class="text-muted">{{ $t('dbAgent.stats.noData') }}</p>
        </div>
      </div>

      <!-- LLM Analysis -->
      <div class="analysis-card analysis-card--full mt-4">
        <div class="analysis-card-header">
          <LIcon size="18" color="accent">llars:robot</LIcon>
          <h3>{{ $t('dbAgent.analysis.title') }}</h3>
          <LBtn variant="accent" size="small" class="ml-auto" @click="runAnalysis" :loading="analysisLoading">
            <LIcon start size="16">llars:wand</LIcon>
            {{ $t('dbAgent.analysis.run') }}
          </LBtn>
        </div>
        <div v-if="analysisResult" class="analysis-result" v-html="renderMarkdown(analysisResult)"></div>
        <p v-else class="text-muted">{{ $t('dbAgent.analysis.hint') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, useRoute } from 'vue-router'
import { marked } from 'marked'
import axios from 'axios'

const { t, locale } = useI18n()
const router = useRouter()
const route = useRoute()

const props = defineProps({
  tab: { type: String, default: null },
})

const validTabs = ['search', 'deals', 'calendar', 'timing', 'analysis']
const initialTab = validTabs.includes(props.tab) ? props.tab : 'search'
const activeTab = ref(initialTab)

const tabs = computed(() => [
  { value: 'search', label: t('dbAgent.tabs.search') },
  { value: 'deals', label: t('dbAgent.tabs.deals') },
  { value: 'calendar', label: t('dbAgent.tabs.calendar') },
  { value: 'timing', label: t('dbAgent.tabs.timing') },
  { value: 'analysis', label: t('dbAgent.tabs.analysis') },
])

// Calendar view mode from query param
const validCalViews = ['year', 'month', 'day']
const calendarView = ref(validCalViews.includes(route.query.view) ? route.query.view : 'month')
const selectedDayDate = ref(route.query.date || toDateInput(new Date(Date.now() + 24 * 60 * 60 * 1000)))

const flexOptions = [
  { label: '0 Tage', value: 0 },
  { label: '±1 Tag', value: 1 },
  { label: '±2 Tage', value: 2 },
  { label: '±3 Tage', value: 3 },
  { label: '±5 Tage', value: 5 },
  { label: '±7 Tage', value: 7 },
]

// Helper: format date as YYYY-MM-DD for date inputs
function toDateInput(d) {
  return d.toISOString().split('T')[0]
}

// State
const status = ref({ running: false, is_scanning: false, scan_count: 0 })
const actionLoading = ref(false)
const deals = ref([])
const dealsLoading = ref(false)
const stats = ref({ has_data: false })
const statsLoading = ref(false)
const calendarData = ref([])
const calendarLoading = ref(false)
const calendarDirection = ref('outbound')
const calendarMonthOffset = ref(0)
const hoveredCalDay = ref(null)
const hoveredTrip = ref(null)
const weekdayData = ref({})
const weekdayLoading = ref(false)
const timingData = ref({})
const timingLoading = ref(false)
const analysisResult = ref('')
const analysisLoading = ref(false)

// Overview (auto-loaded on mount)
const overviewLoading = ref(false)
const overviewDeals = ref([])
const overviewSource = ref('database')

// Station selection
const searchStationFrom = ref('Nürnberg Hbf')
const searchStationTo = ref('Dortmund Hbf')
const stationSuggestions = [
  'Nürnberg Hbf',
  'Dortmund Hbf',
  'Aschaffenburg Hbf',
  'Frankfurt (Main) Hbf',
  'München Hbf',
  'Berlin Hbf',
  'Köln Hbf',
  'Hamburg Hbf',
  'Stuttgart Hbf',
  'Hannover Hbf',
  'Leipzig Hbf',
  'Dresden Hbf',
  'Würzburg Hbf',
  'Erlangen',
  'Fürth (Bay) Hbf',
  'Bamberg',
]

function swapStations() {
  const tmp = searchStationFrom.value
  searchStationFrom.value = searchStationTo.value
  searchStationTo.value = tmp
}

function stationShort(name) {
  if (!name) return '?'
  return name.replace(' Hbf', '').replace(' (Main)', '').replace(' (Bay)', '').slice(0, 3).toUpperCase()
}

// Trip search — pre-fill with next 2 weeks
const now = new Date()
const twoWeeksLater = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000)
const searchDateFrom = ref(toDateInput(new Date(now.getTime() + 24 * 60 * 60 * 1000)))
const searchDateTo = ref(toDateInput(twoWeeksLater))
const searchFlexibility = ref(3)
const searchLoading = ref(false)
const outboundResults = ref([])
const returnResults = ref([])
const selectedOutbound = ref(null)
const selectedReturn = ref(null)

// Keep legacy ref for chat context
const suggestions = computed(() => [...outboundResults.value, ...returnResults.value])

const selectedOutboundJourney = computed(() =>
  selectedOutbound.value != null ? outboundResults.value[selectedOutbound.value] : null
)
const selectedReturnJourney = computed(() =>
  selectedReturn.value != null ? returnResults.value[selectedReturn.value] : null
)
const totalPrice = computed(() => {
  const o = selectedOutboundJourney.value
  const r = selectedReturnJourney.value
  if (o && r) return o.price_eur + r.price_eur
  if (o) return o.price_eur
  if (r) return r.price_eur
  return null
})

// Search history (cached previous searches)
const searchHistory = ref([])
const MAX_SEARCH_HISTORY = 10

function saveCurrentSearch() {
  if (!outboundResults.value.length && !returnResults.value.length) return
  const entry = {
    id: Date.now(),
    dateFrom: searchDateFrom.value,
    dateTo: searchDateTo.value,
    stationFrom: searchStationFrom.value,
    stationTo: searchStationTo.value,
    flexibility: searchFlexibility.value,
    outbound: [...outboundResults.value],
    return: [...returnResults.value],
    chat: [...chatMessages.value],
    selectedOutbound: selectedOutbound.value,
    selectedReturn: selectedReturn.value,
    timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
    cheapestOut: outboundResults.value[0]?.price_eur ?? null,
    cheapestRet: returnResults.value[0]?.price_eur ?? null,
  }
  // Deduplicate: remove existing entry with same params
  searchHistory.value = searchHistory.value.filter(h =>
    !(h.dateFrom === entry.dateFrom && h.dateTo === entry.dateTo
      && h.stationFrom === entry.stationFrom && h.stationTo === entry.stationTo
      && h.flexibility === entry.flexibility)
  )
  searchHistory.value.unshift(entry)
  if (searchHistory.value.length > MAX_SEARCH_HISTORY) searchHistory.value.pop()
}

function restoreSearch(entry) {
  searchDateFrom.value = entry.dateFrom
  searchDateTo.value = entry.dateTo
  searchStationFrom.value = entry.stationFrom
  searchStationTo.value = entry.stationTo
  searchFlexibility.value = entry.flexibility
  outboundResults.value = [...entry.outbound]
  returnResults.value = [...entry.return]
  chatMessages.value = [...entry.chat]
  selectedOutbound.value = entry.selectedOutbound
  selectedReturn.value = entry.selectedReturn
  if (activeTab.value !== 'search') activeTab.value = 'search'
}

function removeSearchHistory(id) {
  searchHistory.value = searchHistory.value.filter(h => h.id !== id)
}

// Follow-up chat
const chatMessages = ref([])
const chatInput = ref('')
const chatLoading = ref(false)
const messagesContainer = ref(null)

// API calls
async function fetchOverview() {
  overviewLoading.value = true
  try {
    const { data } = await axios.get('/api/db-agent/quick-overview')
    if (data.success) {
      overviewDeals.value = data.data.deals || []
      overviewSource.value = data.data.source || 'database'
      if (data.data.status) status.value = data.data.status
      if (data.data.stats) stats.value = data.data.stats
    }
  } catch { /* ignore */ }
  overviewLoading.value = false
}

async function fetchStatus() {
  try {
    const { data } = await axios.get('/api/db-agent/status')
    if (data.success) status.value = data.data
  } catch { /* ignore */ }
}

async function fetchDeals() {
  dealsLoading.value = true
  try {
    const { data } = await axios.get('/api/db-agent/deals?limit=30')
    if (data.success) deals.value = data.data
  } catch { /* ignore */ }
  dealsLoading.value = false
}

async function fetchStats() {
  statsLoading.value = true
  try {
    const { data } = await axios.get('/api/db-agent/stats')
    if (data.success) stats.value = data.data
  } catch { /* ignore */ }
  statsLoading.value = false
}

async function fetchCalendar() {
  calendarLoading.value = true
  try {
    const { data } = await axios.get(`/api/db-agent/calendar?direction=${calendarDirection.value}`)
    if (data.success) calendarData.value = data.data
  } catch { /* ignore */ }
  calendarLoading.value = false
}

async function fetchWeekday() {
  weekdayLoading.value = true
  try {
    const { data } = await axios.get('/api/db-agent/weekday-analysis')
    if (data.success) weekdayData.value = data.data
  } catch { /* ignore */ }
  weekdayLoading.value = false
}

async function fetchTiming() {
  timingLoading.value = true
  try {
    const { data } = await axios.get('/api/db-agent/timing')
    if (data.success) timingData.value = data.data
  } catch { /* ignore */ }
  timingLoading.value = false
}

async function startScheduler() {
  actionLoading.value = true
  try {
    await axios.post('/api/db-agent/scheduler/start')
    await fetchStatus()
  } catch { /* ignore */ }
  actionLoading.value = false
}

async function stopScheduler() {
  actionLoading.value = true
  try {
    await axios.post('/api/db-agent/scheduler/stop')
    await fetchStatus()
  } catch { /* ignore */ }
  actionLoading.value = false
}

async function triggerScan() {
  try {
    await axios.post('/api/db-agent/scan')
    status.value.is_scanning = true
  } catch { /* ignore */ }
}

async function deleteAllData() {
  if (!confirm('Alle historischen Preisdaten löschen? Dies kann nicht rückgängig gemacht werden.')) return
  actionLoading.value = true
  try {
    await axios.delete('/api/db-agent/data')
    overviewDeals.value = []
    deals.value = []
    calendarData.value = []
    outboundResults.value = []
    returnResults.value = []
    await fetchStatus()
  } catch { /* ignore */ }
  actionLoading.value = false
}

// Active search generation — incremented on each new search to cancel stale ones
let activeSearchId = 0

async function searchTrip() {
  if (!searchDateFrom.value || !searchDateTo.value) return

  // Save current results to history before starting new search
  saveCurrentSearch()

  // Cancel any running search by bumping the generation id
  const mySearchId = ++activeSearchId

  searchLoading.value = true
  outboundResults.value = []
  returnResults.value = []
  selectedOutbound.value = null
  selectedReturn.value = null
  chatMessages.value = []

  // Switch to search tab immediately
  if (activeTab.value !== 'search') activeTab.value = 'search'

  // Build date lists with flexibility
  const flex = searchFlexibility.value || 0
  const buildDates = (baseDate) => {
    const dates = []
    const base = new Date(baseDate + 'T00:00:00')
    for (let d = -flex; d <= flex; d++) {
      const dt = new Date(base)
      dt.setDate(dt.getDate() + d)
      if (dt > new Date()) dates.push(dt.toISOString().slice(0, 10))
    }
    return dates
  }

  const outDates = buildDates(searchDateFrom.value)
  const retDates = buildDates(searchDateTo.value)

  // Helper: merge journey into results list, sorted by price, dedup by departure
  const mergeResults = (list, newJourneys) => {
    const seen = new Map()
    for (const j of list) seen.set(j.departure?.slice(0, 16), j)
    for (const j of newJourneys) {
      const key = j.departure?.slice(0, 16)
      if (!seen.has(key) || j.source === 'live') seen.set(key, j)
    }
    return [...seen.values()].sort((a, b) => a.price_eur - b.price_eur)
  }

  // Fetch outbound + return in parallel, each streaming day-by-day
  const fetchDirection = async (dates, direction) => {
    for (const d of dates) {
      // Abort if a newer search was started
      if (activeSearchId !== mySearchId) return
      try {
        const res = await axios.post('/api/db-agent/trip-search-live', { date: d, direction })
        if (activeSearchId !== mySearchId) return
        if (res.data.success && res.data.data.journeys.length) {
          if (direction === 'outbound') {
            outboundResults.value = mergeResults(outboundResults.value, res.data.data.journeys)
          } else {
            returnResults.value = mergeResults(returnResults.value, res.data.data.journeys)
          }
        }
      } catch { /* continue with next day */ }
    }
  }

  await Promise.all([
    fetchDirection(outDates, 'outbound'),
    fetchDirection(retDates, 'return'),
  ])

  // Only finalize if this is still the active search
  if (activeSearchId !== mySearchId) return

  // Auto-welcome message
  const total = outboundResults.value.length + returnResults.value.length
  if (total) {
    const parts = []
    if (outboundResults.value.length) {
      const c = outboundResults.value[0]
      parts.push(`Hinfahrt ab **${c.price_eur.toFixed(2)}€** (${formatDate(c.travel_date)})`)
    }
    if (returnResults.value.length) {
      const c = returnResults.value[0]
      parts.push(`Rückfahrt ab **${c.price_eur.toFixed(2)}€** (${formatDate(c.travel_date)})`)
    }
    chatMessages.value = [{
      role: 'assistant',
      content: `**${total} Verbindungen** gefunden! ${parts.join(', ')}.\n\n`
        + `Wähle je eine Hin- und Rückfahrt aus — der Gesamtpreis wird unten angezeigt.`
    }]
  }
  searchLoading.value = false

  // Save completed search to history
  saveCurrentSearch()
}

// Selection is handled inline via selectedOutbound / selectedReturn

async function sendFollowup() {
  const input = chatInput.value.trim()
  if (!input) return

  chatMessages.value.push({ role: 'user', content: input })
  chatInput.value = ''
  chatLoading.value = true

  await nextTick()
  scrollChat()

  try {
    // Build context for LLM
    const suggestionsContext = suggestions.value.slice(0, 30).map((s, i) => (
      `#${i + 1}: ${formatDate(s.travel_date)} ${s.direction === 'outbound' ? 'DO→N' : 'N→DO'} `
      + `${formatTime(s.departure)}-${formatTime(s.arrival)} ${s.price_eur}€ `
      + `${s.is_direct ? 'Direkt' : s.transfers + ' Umst.'} ${s.train_types}`
    )).join('\n')

    const systemPrompt = `Du bist ein hilfreicher Deutsche Bahn Reiseberater. Du hast folgende Verbindungen gefunden (Dortmund Hbf ↔ Nuernberg Hbf, BahnCard 25, 2. Klasse):\n\n${suggestionsContext}\n\n`
      + `Antworte kurz und praeise auf Deutsch. Wenn der Nutzer nach alternativen Daten fragt, schlage passende Vorschlaege aus der Liste vor. `
      + `Nenne immer die Vorschlags-Nummer (#N). Wenn ein Datum nicht in der Liste ist, sage das ehrlich.`

    const { data } = await axios.post('/api/db-agent/analyze', {
      date_from: searchDateFrom.value,
      date_to: searchDateTo.value,
      _chat_mode: true,
      _system_prompt: systemPrompt,
      _user_message: input,
      _chat_history: chatMessages.value.slice(-10),
    })
    if (data.success) {
      chatMessages.value.push({ role: 'assistant', content: data.data.analysis })
    }
  } catch {
    chatMessages.value.push({ role: 'assistant', content: 'Entschuldigung, bei der Analyse ist ein Fehler aufgetreten.' })
  }
  chatLoading.value = false
  await nextTick()
  scrollChat()
}

function scrollChat() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function runAnalysis() {
  analysisLoading.value = true
  analysisResult.value = ''
  try {
    const payload = {}
    if (searchDateFrom.value) payload.date_from = searchDateFrom.value
    if (searchDateTo.value) payload.date_to = searchDateTo.value
    const { data } = await axios.post('/api/db-agent/analyze', payload)
    if (data.success) analysisResult.value = data.data.analysis
  } catch { /* ignore */ }
  analysisLoading.value = false
}

// Helpers
function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit' })
}

function formatTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

function formatShortDate(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
}

function formatWeekday(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { weekday: 'short' })
}

function priceClass(price) {
  if (price < 30) return 'price-cheap'
  if (price < 60) return 'price-medium'
  if (price < 100) return 'price-expensive'
  return 'price-very-expensive'
}

function weekdayBarWidth(avg) {
  const max = Math.max(...Object.values(weekdayData.value).map(d => d.avg), 1)
  return Math.round((avg / max) * 100)
}

// Timing analysis helpers
function timingBarWidth(avg, list) {
  const max = Math.max(...list.map(d => d.avg), 1)
  return Math.round((avg / max) * 100)
}

const timingTips = computed(() => {
  const d = timingData.value
  if (!d.has_data) return []
  const tips = []

  // Best lead time bucket
  if (d.lead_time?.length) {
    const best = d.lead_time.reduce((a, b) => a.avg < b.avg ? a : b)
    tips.push({ key: 'leadTime', bucket: best.bucket, price: best.avg })
  }
  // Best departure time
  if (d.departure_time?.length) {
    const best = d.departure_time.reduce((a, b) => a.avg < b.avg ? a : b)
    tips.push({ key: 'departure', slot: best.slot, price: best.avg })
  }
  // Transfers saving
  if (d.transfers?.length >= 2) {
    const direct = d.transfers.find(t => t.transfers === 0)
    const cheapest = d.transfers.reduce((a, b) => a.avg < b.avg ? a : b)
    if (direct && cheapest.transfers > 0) {
      const pct = Math.round((1 - cheapest.avg / direct.avg) * 100)
      if (pct > 0) tips.push({ key: 'transfers', label: cheapest.label, percent: pct })
    }
  }
  return tips
})

// Calendar view helpers
function openDayView(dateStr) {
  selectedDayDate.value = dateStr
  calendarView.value = 'day'
}

function goToMonth(offset) {
  calendarMonthOffset.value = offset
  calendarView.value = 'month'
}

function goToDay(dateStr) {
  selectedDayDate.value = dateStr
  calendarView.value = 'day'
}

function navigateDayView(delta) {
  if (!selectedDayDate.value) return
  const d = new Date(selectedDayDate.value)
  d.setDate(d.getDate() + delta)
  selectedDayDate.value = toDateInput(d)
}

function formatDateLong(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleDateString(locale.value === 'de' ? 'de-DE' : 'en-US', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })
}

// Calendar computations
const weekdayHeaders = computed(() => {
  const days = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
  return days
})

const calendarMonthLabel = computed(() => {
  const d = new Date()
  d.setDate(1)
  d.setMonth(d.getMonth() + calendarMonthOffset.value)
  return d.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' })
})

const calendarCells = computed(() => {
  const d = new Date()
  d.setDate(1)
  d.setMonth(d.getMonth() + calendarMonthOffset.value)
  const year = d.getFullYear()
  const month = d.getMonth()

  const firstDay = new Date(year, month, 1)
  // Monday=0, Sunday=6
  let startDow = firstDay.getDay() - 1
  if (startDow < 0) startDow = 6

  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  // Build price lookup from calendarData
  const priceLookup = {}
  for (const c of calendarData.value) {
    priceLookup[c.date] = c
  }

  const cells = []
  // Empty cells before first day
  for (let i = 0; i < startDow; i++) {
    cells.push({ date: null })
  }
  // Day cells
  for (let day = 1; day <= daysInMonth; day++) {
    const dateObj = new Date(year, month, day)
    const dateStr = dateObj.toISOString().split('T')[0]
    const priceInfo = priceLookup[dateStr]
    cells.push({
      date: dateStr,
      dayNum: day,
      isToday: dateObj.getTime() === today.getTime(),
      isPast: dateObj < today,
      cheapest: priceInfo ? priceInfo.cheapest : null,
      average: priceInfo ? priceInfo.average : null,
      std_dev: priceInfo ? priceInfo.std_dev : 0,
      count: priceInfo ? priceInfo.count : 0,
    })
  }
  return cells
})

// Build trip strips: find best outbound+return combos
const calendarTrips = computed(() => {
  if (!calendarData.value.length) return []

  // We need both outbound AND return data for trips
  // For now, use calendarData (which is one direction) to show price strips
  // Trip strips are best when we have deals from the overview
  if (!overviewDeals.value.length && !deals.value.length) return []

  const allDeals = overviewDeals.value.length ? overviewDeals.value : deals.value
  const outbound = allDeals.filter(d => d.direction === 'outbound')
  const returns = allDeals.filter(d => d.direction === 'return')

  if (!outbound.length || !returns.length) return []

  const trips = []
  // Pair cheapest outbound with cheapest return (return must be after outbound)
  for (const out of outbound.slice(0, 8)) {
    for (const ret of returns.slice(0, 8)) {
      const outDate = out.travel_date
      const retDate = ret.travel_date
      if (retDate > outDate) {
        const daysDiff = Math.round((new Date(retDate) - new Date(outDate)) / (1000 * 60 * 60 * 24))
        if (daysDiff >= 1 && daysDiff <= 14) {
          trips.push({
            outDate,
            retDate,
            days: daysDiff,
            totalPrice: out.price_eur + ret.price_eur,
            outPrice: out.price_eur,
            retPrice: ret.price_eur,
            outDeparture: out.departure,
            outArrival: out.arrival,
            retDeparture: ret.departure,
            retArrival: ret.arrival,
            outTrains: out.train_types || '',
            retTrains: ret.train_types || '',
          })
        }
      }
    }
  }
  // Sort by total price and limit
  trips.sort((a, b) => a.totalPrice - b.totalPrice)
  return trips.slice(0, 5)
})

// Year view: 12 months of mini calendars
const yearMonths = computed(() => {
  const priceLookup = {}
  for (const c of calendarData.value) {
    priceLookup[c.date] = c
  }

  const months = []
  const now = new Date()
  for (let m = 0; m < 12; m++) {
    const d = new Date(now.getFullYear(), now.getMonth() + m, 1)
    const year = d.getFullYear()
    const month = d.getMonth()
    const daysInMonth = new Date(year, month + 1, 0).getDate()
    let startDow = d.getDay() - 1
    if (startDow < 0) startDow = 6

    const cells = []
    for (let i = 0; i < startDow; i++) cells.push({ date: null })
    let monthCheapest = null
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = new Date(year, month, day).toISOString().split('T')[0]
      const info = priceLookup[dateStr]
      const cheapest = info ? info.cheapest : null
      if (cheapest != null && (monthCheapest == null || cheapest < monthCheapest)) {
        monthCheapest = cheapest
      }
      cells.push({ date: dateStr, dayNum: day, cheapest, average: info?.average, count: info?.count, std_dev: info?.std_dev })
    }

    const offset = month - now.getMonth() + (year - now.getFullYear()) * 12
    months.push({
      key: `${year}-${month}`,
      label: d.toLocaleDateString(locale.value === 'de' ? 'de-DE' : 'en-US', { month: 'short', year: 'numeric' }),
      offset,
      cells,
      cheapest: monthCheapest,
    })
  }
  return months
})

// Day view: all connections for a single date
const dayViewData = computed(() => {
  if (!selectedDayDate.value) return []
  // Try from deals or overview data
  const allDeals = [...(overviewDeals.value || []), ...(deals.value || [])]
  const dayEntries = allDeals.filter(d => d.travel_date === selectedDayDate.value)
  dayEntries.sort((a, b) => a.price_eur - b.price_eur)
  return dayEntries
})

const dayViewPriceInfo = computed(() => {
  if (!selectedDayDate.value) return null
  return calendarData.value.find(c => c.date === selectedDayDate.value) || null
})


function buildBahnLink(journey) {
  const from = journey.direction === 'outbound' ? searchStationFrom.value : searchStationTo.value
  const to = journey.direction === 'outbound' ? searchStationTo.value : searchStationFrom.value
  const dep = new Date(journey.departure)
  const iso = dep.getFullYear() + '-' +
    String(dep.getMonth() + 1).padStart(2, '0') + '-' +
    String(dep.getDate()).padStart(2, '0') + 'T' +
    String(dep.getHours()).padStart(2, '0') + ':' +
    String(dep.getMinutes()).padStart(2, '0') + ':00'
  return `https://www.bahn.de/buchung/fahrplan/suche#so=${encodeURIComponent(from)}&zo=${encodeURIComponent(to)}&soid=O%3D${encodeURIComponent(from)}&zoid=O%3D${encodeURIComponent(to)}&hd=${iso}&s=true&d=false&ar=false`
}

function renderMarkdown(text) {
  return marked.parse(text || '')
}

// Watch — sync tab with URL
watch(activeTab, (tab) => {
  // Update URL when tab changes
  const currentPath = `/db-agent/${tab}`
  const query = {}
  if (tab === 'calendar') {
    if (calendarView.value !== 'month') query.view = calendarView.value
    if (selectedDayDate.value) query.date = selectedDayDate.value
  }
  if (route.path !== currentPath || JSON.stringify(route.query) !== JSON.stringify(query)) {
    router.replace({ path: currentPath, query })
  }

  if (tab === 'deals' && !deals.value.length) fetchDeals()
  if (tab === 'calendar' && !calendarData.value.length) fetchCalendar()
  if (tab === 'timing' && !timingData.value.has_data) fetchTiming()
  if (tab === 'analysis') {
    if (!stats.value.has_data) fetchStats()
    if (!Object.keys(weekdayData.value).length) fetchWeekday()
  }
})

// Sync calendar view mode with URL query
watch(calendarView, (view) => {
  const query = { ...route.query }
  if (view === 'month') {
    delete query.view
  } else {
    query.view = view
  }
  router.replace({ path: route.path, query })
})

watch(selectedDayDate, (dateStr) => {
  const query = { ...route.query }
  if (dateStr) {
    query.date = dateStr
    query.view = 'day'
    calendarView.value = 'day'
  } else {
    delete query.date
  }
  router.replace({ path: route.path, query })
})

// React to route param changes (e.g. browser back/forward)
watch(() => props.tab, (newTab) => {
  if (newTab && validTabs.includes(newTab) && activeTab.value !== newTab) {
    activeTab.value = newTab
  }
})

watch(calendarDirection, () => fetchCalendar())
watch(calendarMonthOffset, () => fetchCalendar())

onMounted(() => {
  // Always load overview (status + deals for search tab)
  fetchOverview()

  // If landing directly on a non-search tab, load its data too
  const tab = activeTab.value
  if (tab === 'deals') fetchDeals()
  if (tab === 'calendar') fetchCalendar()
  if (tab === 'timing') fetchTiming()
  if (tab === 'analysis') {
    fetchStats()
    fetchWeekday()
  }
})
</script>

<style scoped>
.db-agent-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

/* ===== Header ===== */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-text .title {
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0;
  line-height: 1.2;
}

.header-text .subtitle {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-content {
  margin-top: 16px;
}

/* ===== Search Bar ===== */
.search-bar {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 16px 4px 16px 4px;
  padding: 16px;
  margin-bottom: 20px;
}

.search-fields {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.date-field {
  max-width: 170px;
  flex-shrink: 0;
}

.flex-field {
  max-width: 130px;
  flex-shrink: 0;
}

.search-arrow {
  opacity: 0.4;
}

.search-stations {
  margin-bottom: 4px;
}

.station-field {
  flex: 1;
  min-width: 160px;
}

.swap-btn {
  flex-shrink: 0;
  opacity: 0.6;
  transition: opacity 0.15s;
}
.swap-btn:hover {
  opacity: 1;
}

.search-leg {
  display: flex;
  align-items: center;
  gap: 6px;
}
.search-leg-label {
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
}

/* ===== Split Panels ===== */
.trip-split-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.trip-panel {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
}

.trip-panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  font-weight: 600;
  font-size: 0.9rem;
}
.trip-panel-header--outbound {
  background: rgba(var(--v-theme-primary), 0.08);
  border-bottom: 2px solid rgba(var(--v-theme-primary), 0.2);
}
.trip-panel-header--return {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-bottom: 2px solid rgba(var(--v-theme-on-surface), 0.1);
}
.trip-panel-date {
  margin-left: auto;
  font-size: 0.8rem;
  opacity: 0.7;
}

.trip-panel-list {
  max-height: 420px;
  overflow-y: auto;
  padding: 8px;
}

.suggestion-card--compact {
  padding: 8px 12px;
}
.suggestion-card--compact .suggestion-number {
  font-size: 0.75rem;
  min-width: 24px;
}
.suggestion-card--compact .suggestion-price {
  font-size: 1rem;
}

.empty-state-small {
  padding: 24px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* ===== Total Price Bar ===== */
.trip-total-bar {
  background: rgba(var(--v-theme-primary), 0.06);
  border: 2px solid rgba(var(--v-theme-primary), 0.2);
  border-radius: 16px 4px 16px 4px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.trip-total-selections {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.trip-total-leg {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}
.trip-total-leg--empty {
  opacity: 0.5;
}

.trip-total-price {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
.trip-total-label {
  font-size: 0.85rem;
  font-weight: 600;
  opacity: 0.7;
}
.trip-total-amount {
  font-size: 1.6rem;
  font-weight: 800;
}
.bahn-link-lg {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-primary), 0.8);
  text-decoration: none;
  padding: 4px 10px;
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
  border-radius: 6px 2px 6px 2px;
  transition: all 0.15s;
}
.bahn-link-lg:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  text-decoration: none;
}

/* ===== Section Header ===== */
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.section-header h2 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

/* ===== Suggestion Cards ===== */
.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.suggestion-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 8px 3px 8px 3px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.suggestion-card:hover {
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-color: rgba(var(--v-theme-primary), 0.3);
  transform: translateX(2px);
}

.suggestion-card--selected {
  border-color: rgba(var(--v-theme-primary), 0.5);
  background: rgba(var(--v-theme-primary), 0.05);
}

.suggestion-card--night {
  border-left: 3px solid #1a237e;
  background: rgba(26, 35, 126, 0.04);
}
.suggestion-card--night:hover {
  background: rgba(26, 35, 126, 0.08);
}
.suggestion-card--night.suggestion-card--selected {
  border-color: #1a237e;
  border-left: 3px solid #1a237e;
  background: rgba(26, 35, 126, 0.08);
}

.night-badge {
  display: inline-flex;
  align-items: center;
  color: #1a237e;
  opacity: 0.85;
}

.suggestion-number {
  font-size: 0.75rem;
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.4);
  min-width: 28px;
  text-align: center;
}

.suggestion-main {
  flex: 1;
  min-width: 0;
}

.suggestion-route {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.suggestion-details {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.85rem;
  flex-wrap: wrap;
}

.suggestion-date,
.suggestion-time {
  display: flex;
  align-items: center;
  gap: 3px;
}

.suggestion-duration {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.8rem;
}

.suggestion-trains {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
  margin-top: 2px;
}

.suggestion-price-col {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  min-width: 80px;
}

.suggestion-price {
  font-size: 1.2rem;
  font-weight: 700;
  min-width: 70px;
  text-align: right;
}

.bahn-link {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-primary), 0.8);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0.7;
  transition: opacity 0.15s;
}
.bahn-link:hover {
  opacity: 1;
  text-decoration: underline;
}

/* ===== Follow-up Chat ===== */
.followup-section {
  margin-top: 24px;
}

.followup-messages {
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
  padding: 4px;
}

.chat-message {
  display: flex;
  gap: 8px;
  max-width: 85%;
}

.chat-message--user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.chat-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-bubble {
  padding: 10px 14px;
  border-radius: 12px 4px 12px 4px;
  font-size: 0.88rem;
  line-height: 1.5;
}

.chat-message--assistant .chat-bubble {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.chat-message--user .chat-bubble {
  background: rgba(var(--v-theme-primary), 0.1);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.chat-bubble :deep(p) {
  margin: 0 0 4px;
}

.chat-bubble :deep(strong) {
  color: rgb(var(--v-theme-primary));
}

.followup-input {
  display: flex;
  gap: 8px;
}

/* ===== Price Colors ===== */
.price-cheap { color: #4caf50; }
.price-medium { color: #ff9800; }
.price-expensive { color: #f44336; }
.price-very-expensive { color: #b71c1c; }

/* ===== Calendar Controls ===== */
.calendar-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
}

.calendar-month-label {
  font-weight: 600;
  font-size: 0.9rem;
  min-width: 140px;
  text-align: center;
}

/* ===== Real Calendar ===== */
.real-calendar {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  overflow: hidden;
}

.cal-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.cal-header-cell {
  padding: 8px 4px;
  text-align: center;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.cal-body {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  position: relative;
}

.cal-cell {
  position: relative;
  min-height: 72px;
  padding: 6px 8px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.05);
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.05);
  transition: background 0.15s ease;
}

.cal-cell:nth-child(7n) {
  border-right: none;
}

.cal-cell--empty {
  background: rgba(var(--v-theme-on-surface), 0.01);
}

.cal-cell--today {
  outline: 2px solid rgba(var(--v-theme-primary), 0.5);
  outline-offset: -2px;
}

.cal-cell--past {
  opacity: 0.4;
}

.cal-cell.price-cheap {
  background: rgba(76, 175, 80, 0.08);
}

.cal-cell.price-medium {
  background: rgba(255, 152, 0, 0.08);
}

.cal-cell.price-expensive {
  background: rgba(244, 67, 54, 0.08);
}

.cal-cell.price-very-expensive {
  background: rgba(183, 28, 28, 0.08);
}

.cal-cell:not(.cal-cell--empty):hover {
  background: rgba(var(--v-theme-primary), 0.06);
}

.cal-day-num {
  display: block;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.cal-day-price {
  display: block;
  font-size: 0.95rem;
  font-weight: 700;
  margin-top: 2px;
}

.cal-day-sigma {
  display: block;
  font-size: 0.6rem;
  color: rgba(var(--v-theme-on-surface), 0.35);
}

.cal-day-sigma--high {
  color: #f44336;
  font-weight: 600;
}

/* ===== Trip Recommendations ===== */
.trip-strips {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.trip-strip-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px 3px 8px 3px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid transparent;
}

.trip-strip-card.price-cheap {
  background: rgba(76, 175, 80, 0.06);
  border-color: rgba(76, 175, 80, 0.2);
}

.trip-strip-card.price-medium {
  background: rgba(255, 152, 0, 0.06);
  border-color: rgba(255, 152, 0, 0.2);
}

.trip-strip-card.price-expensive {
  background: rgba(244, 67, 54, 0.06);
  border-color: rgba(244, 67, 54, 0.2);
}

.trip-strip-card:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.trip-strip-rank {
  font-size: 0.75rem;
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.4);
  min-width: 24px;
}

.trip-strip-dates {
  min-width: 160px;
}

.trip-strip-range {
  display: block;
  font-weight: 600;
  font-size: 0.85rem;
}

.trip-strip-days {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.trip-strip-legs {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.trip-strip-leg {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
}

.trip-strip-leg-price {
  font-weight: 600;
}

.trip-strip-total {
  font-size: 1.1rem;
  font-weight: 700;
  min-width: 80px;
  text-align: right;
}

.trip-strip-total-label {
  display: block;
  font-size: 0.6rem;
  font-weight: 400;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* ===== Year View ===== */
.year-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.year-month-card {
  padding: 10px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px 3px 8px 3px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.year-month-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  background: rgba(var(--v-theme-primary), 0.03);
  transform: translateY(-2px);
}

.year-month-name {
  font-weight: 600;
  font-size: 0.8rem;
  margin-bottom: 6px;
  text-transform: capitalize;
}

.year-month-mini-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
}

.year-mini-cell {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 2px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.1s;
}
.year-mini-cell:not(.year-mini-cell--empty):hover {
  transform: scale(1.8);
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.3);
  z-index: 2;
  position: relative;
}

.year-mini-cell--empty {
  background: transparent;
}

.year-mini-cell.price-cheap { background: rgba(76, 175, 80, 0.35); }
.year-mini-cell.price-medium { background: rgba(255, 152, 0, 0.35); }
.year-mini-cell.price-expensive { background: rgba(244, 67, 54, 0.35); }
.year-mini-cell.price-very-expensive { background: rgba(183, 28, 28, 0.35); }

.year-month-summary {
  margin-top: 6px;
  font-size: 0.75rem;
  text-align: center;
  font-weight: 600;
}

/* ===== Day View ===== */
.day-view-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px 3px 8px 3px;
}

/* ===== Calendar Legend ===== */
.calendar-legend {
  display: flex;
  gap: 16px;
  font-size: 0.8rem;
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px 1px 3px 1px;
}

.legend-dot.price-cheap { background: rgba(76, 175, 80, 0.4); }
.legend-dot.price-medium { background: rgba(255, 152, 0, 0.4); }
.legend-dot.price-expensive { background: rgba(244, 67, 54, 0.4); }
.legend-dot.price-very-expensive { background: rgba(183, 28, 28, 0.4); }

/* ===== Timing Tab ===== */
.timing-tips {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.timing-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(76, 175, 80, 0.06);
  border: 1px solid rgba(76, 175, 80, 0.2);
  border-radius: 8px 3px 8px 3px;
  font-size: 0.85rem;
  font-weight: 500;
}

.timing-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 900px) {
  .timing-grid { grid-template-columns: 1fr; }
}

.timing-card {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
}

.timing-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.timing-card-header h3 {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
}

.timing-hint {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
  margin: 0 0 12px;
}

.timing-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.timing-bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.timing-bar-label {
  width: 90px;
  font-size: 0.8rem;
  font-weight: 500;
  flex-shrink: 0;
  text-align: right;
}

.timing-bar-track {
  flex: 1;
  height: 8px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 4px;
  overflow: hidden;
}

.timing-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.timing-bar-fill.price-cheap { background: rgba(76, 175, 80, 0.5); }
.timing-bar-fill.price-medium { background: rgba(255, 152, 0, 0.5); }
.timing-bar-fill.price-expensive { background: rgba(244, 67, 54, 0.5); }
.timing-bar-fill.price-very-expensive { background: rgba(183, 28, 28, 0.5); }

.timing-bar-value {
  font-weight: 600;
  font-size: 0.85rem;
  min-width: 65px;
  text-align: right;
  flex-shrink: 0;
}

.timing-bar-meta {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
  min-width: 90px;
  flex-shrink: 0;
}

/* ===== Analysis Cards ===== */
.analysis-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 768px) {
  .analysis-cards { grid-template-columns: 1fr; }
}

.analysis-card {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
}

.analysis-card--full {
  grid-column: 1 / -1;
}

.analysis-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.analysis-card-header h3 {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.04);
}

.stat-label {
  font-weight: 500;
  font-size: 0.85rem;
}

.weekday-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.weekday-name {
  width: 80px;
  font-size: 0.85rem;
  font-weight: 500;
}

.weekday-bar {
  height: 6px;
  background: rgba(var(--v-theme-primary), 0.25);
  border-radius: 3px;
  min-width: 4px;
  transition: width 0.3s ease;
}

.weekday-price {
  font-weight: 600;
  font-size: 0.85rem;
  min-width: 55px;
  text-align: right;
}

.analysis-result {
  font-size: 0.9rem;
  line-height: 1.65;
}

.analysis-result :deep(h1),
.analysis-result :deep(h2),
.analysis-result :deep(h3) {
  margin-top: 14px;
  margin-bottom: 6px;
  font-size: 1rem;
}

.analysis-result :deep(ul) {
  padding-left: 18px;
}

.text-muted {
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.85rem;
}

/* ===== Overview Loading ===== */
.overview-loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.overview-section {
  margin-bottom: 4px;
}

/* ===== Empty State ===== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}
</style>

<style>
/* Year cell tooltip (unscoped — rendered in Vuetify overlay) */
.year-cell-tooltip {
  background: rgba(var(--v-theme-surface), 0.97) !important;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px 2px 8px 2px !important;
  padding: 0 !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.year-cell-tooltip .year-tooltip-content {
  padding: 8px 12px;
  min-width: 140px;
}
.year-cell-tooltip .year-tooltip-date {
  font-weight: 600;
  font-size: 0.8rem;
  margin-bottom: 6px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  padding-bottom: 4px;
}
.year-cell-tooltip .year-tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.78rem;
  line-height: 1.6;
}
.year-cell-tooltip .year-tooltip-row strong {
  font-weight: 700;
}
.year-cell-tooltip .price-cheap { color: #4caf50; }
.year-cell-tooltip .price-medium { color: #ff9800; }
.year-cell-tooltip .price-expensive { color: #f44336; }
.year-cell-tooltip .price-very-expensive { color: #b71c1c; }

/* ===== Search History ===== */
.search-history-section {
  margin-top: 24px;
}
.search-history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.search-history-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 6px 2px 6px 2px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.search-history-card:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  border-color: rgba(var(--v-theme-primary), 0.3);
}
.search-history-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.search-history-route {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.search-history-dates {
  font-size: 0.85rem;
  font-weight: 500;
}
.search-history-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.8rem;
  opacity: 0.8;
}
.search-history-price {
  font-weight: 600;
}
.search-history-count {
  opacity: 0.6;
}
.search-history-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.search-history-time {
  font-size: 0.75rem;
  opacity: 0.5;
}
</style>
