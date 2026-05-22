import { useLanguage } from '../contexts/LanguageContext'

interface Props {
  floor: number
  yearBuilt: number
}

export default function MadridElevatorRisk({ floor, yearBuilt }: Props) {
  const { lang } = useLanguage()
  const isZh = lang === 'zh'

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-xs text-amber-800 space-y-1">
      <p className="font-semibold text-sm">
        {isZh
          ? `${yearBuilt}年建造 · ${floor}楼 · 无电梯 — 潜在电梯改造摊派风险`
          : `Built ${yearBuilt} · Floor ${floor} · No elevator — latent elevator derrama risk`}
      </p>
      <p>
        {isZh
          ? `根据修订后的《水平产权法》，楼内任何70岁以上或残障业主均可依法要求安装电梯，无需整栋楼同意。马德里住宅楼安装电梯费用约4万–18万欧元（由全体业主分摊），政府补贴40–75%后，个人承担部分仍可能达5,000–25,000欧元。`
          : `Under the reformed Ley de Propiedad Horizontal, any owner over 70 or with a disability can legally demand elevator installation. Installing an elevator in a Madrid building costs €40,000–€180,000 split among owners. After subsidies (40–75%), each owner's share can still reach €5,000–€25,000.`}
      </p>
      <p className="font-medium">
        {isZh
          ? '行动：购房前询问楼内是否有老年或残障业主曾讨论电梯安装，将此风险纳入持有成本。'
          : 'Action: Before signing, ask whether any elderly or disabled owners are present and have discussed elevator installation. Budget this as a potential future expense.'}
      </p>
    </div>
  )
}
