# Deneyin kural metni

`security-rules.md`, K1–K4 koşullarında ajana verilen güvenlik kurallarıdır. Bütün senaryolarda ve iki ajanda aynı metin kullanılır (ADR-0020, öneri).

| Koşul | Metin nasıl kullanılır |
|---|---|
| K0 | Kullanılmaz |
| K1 | Çalışma klasörüne `CLAUDE.md` (Claude Code) ya da `AGENTS.md` (Antigravity) olarak konur; başka bir şey yapılmaz |
| K2 | K1 ile aynı, ayrıca genel Semgrep hook'u |
| K3, K4 | K1 ile aynı, ayrıca bu metinden `sdguard compile` ile derlenen paket (`.sdguard/`, salt okunur) |

## Nasıl yazıldı
- **Kaynak:** `ZAFIYET_KATALOGU.md` §2–4'teki CWE listesi (BaxBench'in havuzdaki CWE'leri, defterin beş invariant ailesi, CWE-862/639) ve gerçek CLAUDE.md dosyalarında sık görülen güvenlik maddelerinin dili. Exploit kodundan ya da tur istemlerinden türetilmedi.
- **Senaryodan bağımsız.** Hiçbir senaryonun uç noktasını, alan adını ya da tur yapısını anmaz. Test bölmesi için ayrı metin yazılmaz; böylece metin test senaryolarına göre ayarlanmış olamaz.
- **Gerçekçi bir karışım.** Ajanın eylemlerine (izin), koda (Semgrep) ve çalışan servise (test) dair maddeler var; "Validate all input." gibi bilerek muğlak maddeler de var. Gerçek dosyalarda bunlar da bulunuyor ve derleyicinin onları tavsiye olarak bırakması ölçülen bir sonuç.
- **İşlev gereksinimleriyle çelişmez.** Kimlik doğrulama maddesi "when the service has user accounts" diye koşullu yazıldı. Senaryo 1'in 1. turunda hesap yok; koşulsuz yazılsaydı K1'deki ajan 1. turda istemde olmayan bir giriş zorunluluğu ekleyip işlev testlerinden kalabilirdi.
- **Yalnızca güvenlik.** Derleme komutu, kod stili gibi maddeler bilerek yok. Olsaydı K1 ile K0 arasındaki fark yalnızca güvenlik kuralları olmazdı.

## Geçerlilik notu
Metni exploit'leri yazan kişi (Ege) yazdı. Kurallar exploit'lerle aynı CWE'leri kapsıyor; bu bilerek böyle, çünkü deney "yazılı kural korunuyor mu" sorusunu soruyor. Yine de K1/K3'ün başarısı metnin exploit'lere ne kadar yakın olduğuna bağlı. Önlemler:
- Metin, ilk K1 oturumundan önce dondurulur ve sha256'sı `config_fingerprint`'e girer.
- Deniz bağımsız olarak inceler (#27).
- Korpus B (RQ1) toplandığında maddelerin gerçek dosyalardaki karşılıkları raporlanır.

## Değiştirmek
G1'den sonra değişirse pilot sonuçları yeni metinle karşılaştırılamaz. Değişiklik `DECISIONS.md`'ye yazılır.
