import { useLanguage } from '../contexts/LanguageContext'

interface Props {
  yearBuilt: number
  iteStatus?: string
}

export default function MadridITERiskFlag({ yearBuilt, iteStatus }: Props) {
  const { lang } = useLanguage()
  const isZh = lang === 'zh'
  const isUnfavorable = iteStatus === 'DESFAVORABLE'
  const isUnknown = !iteStatus || iteStatus === 'UNKNOWN'

  if (!isUnfavorable && !isUnknown) return null

  const cls = isUnfavorable
    ? 'bg-red-50 border-red-200 text-red-800'
    : 'bg-amber-50 border-amber-200 text-amber-800'
  const iconCls = isUnfavorable ? 'text-red-500' : 'text-amber-500'

  return (
    <div className={`rounded-xl border px-4 py-3 text-xs space-y-1.5 ${cls}`}>
      <div className="flex items-start gap-2">
        <span className={`text-sm shrink-0 ${iconCls}`}>
          {isUnfavorable ? '🔴' : '⚠'}
        </span>
        <div className="space-y-1">
          <p className="font-semibold text-sm">
            {isUnfavorable
              ? (isZh ? `ITE检查结果【不合格】— 建于${yearBuilt}年` : `ITE inspection UNFAVORABLE — Built ${yearBuilt}`)
              : (isZh ? `建于${yearBuilt}年：马德里ITE检查风险` : `Built ${yearBuilt}: Madrid ITE inspection risk`)}
          </p>
          <p>
            {isUnfavorable
              ? (isZh
                  ? '本楼ITE建筑技术检查结果不合格，存在强制整改义务，费用由全体业主分摊。购房后你将共同承担这笔费用。'
                  : 'This building has an UNFAVORABLE ITE (Inspección Técnica de Edificios) result. Mandatory rehabilitation works are pending — costs are split among all owners.')
              : (isZh
                  ? '马德里中心区约40%的1975年前建筑ITE检查结果不合格。该建筑ITE状态无法从公开数据确认。'
                  : '~40% of pre-1975 Madrid buildings in central districts have adverse ITE results. This building\'s ITE status could not be confirmed from available data.')}
          </p>
          <p className="font-medium">
            {isZh
              ? '行动：签约前向卖方或楼栋管理员索取完整ITE报告，了解整改内容、费用及截止日期。'
              : 'Action: Request the full ITE report from seller or building administrator before signing arras. Understand what works are required, their cost, and the deadline.'}
          </p>
        </div>
      </div>
    </div>
  )
}
