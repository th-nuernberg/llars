import { i18n } from '@/i18n'

export function logI18n(level, key, ...args) {
  const logger = console[level] || console.log
  const message = i18n.global.t(key)

  if (args.length > 0) {
    logger(message, ...args)
  } else {
    logger(message)
  }
}

export function logI18nParams(level, key, params, ...args) {
  const logger = console[level] || console.log
  const message = i18n.global.t(key, params)

  if (args.length > 0) {
    logger(message, ...args)
  } else {
    logger(message)
  }
}
