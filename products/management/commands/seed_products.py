from decimal import Decimal
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Category, Product

IMAGES_DIR = Path(__file__).resolve().parents[2] / 'seed_data' / 'images'

# (slug, name, parent_slug)
CATEGORIES = [
    ('bike', 'Велосипеды', None),
    ('shosseynye', 'Шоссейные', 'bike'),
    ('mtb', 'Горные (MTB)', 'bike'),
    ('grevel', 'Гревел', 'bike'),
    ('skladnye', 'Складные', 'bike'),
    ('gorodskie', 'Городские', 'bike'),

    ('zapchasti', 'Запчасти', None),
    ('frame', 'Рамы', 'zapchasti'),
    ('shiny', 'Шины', 'zapchasti'),
    ('kamery', 'Камеры', 'zapchasti'),
    ('transmissiya', 'Трансмиссия', 'zapchasti'),
    ('tormoza', 'Тормоза', 'zapchasti'),
    ('pedali', 'Педали', 'zapchasti'),
    ('sedla', 'Сёдла', 'zapchasti'),

    ('aksessuary', 'Аксессуары', None),
    ('fonari', 'Фонари', 'aksessuary'),
    ('shlemy', 'Шлемы', 'aksessuary'),
    ('zamki', 'Замки', 'aksessuary'),
    ('nasosy', 'Насосы', 'aksessuary'),
    ('velokompyutery', 'Велокомпьютеры', 'aksessuary'),
    ('flyagoderzhateli', 'Флягодержатели', 'aksessuary'),
]

# (slug, name, category_slug, price, stock, description); картинка — seed_data/images/<slug>.jpg
PRODUCTS = [
    # Шоссейные
    ('giant-tcr-advanced-2', 'Giant TCR Advanced 2', 'shosseynye', 245000, 4,
     'Карбоновая шоссейная рама, группа Shimano 105 2x12, дисковые гидравлические тормоза, колёса 700C.'),
    ('canyon-ultimate-cf-sl-7', 'Canyon Ultimate CF SL 7', 'shosseynye', 265000, 3,
     'Лёгкий карбоновый шоссейник для гонок и длинных заездов. Shimano 105 Di2, вес около 8 кг.'),
    ('specialized-allez-sport', 'Specialized Allez Sport', 'shosseynye', 125000, 6,
     'Алюминиевая рама E5, карбоновая вилка, Shimano Sora 2x9. Отличный первый шоссейный велосипед.'),
    ('trek-emonda-alr-5', 'Trek Émonda ALR 5', 'shosseynye', 195000, 2,
     'Алюминиевая рама с гоночной геометрией, Shimano 105, дисковые тормоза, покрышки 700x28.'),
    # Горные
    ('giant-talon-2-29', 'Giant Talon 2 29', 'mtb', 78000, 8,
     'Хардтейл для трейлов, колёса 29", вилка SR Suntour 100 мм, Shimano Deore 1x10, гидравлические тормоза.'),
    ('canyon-spectral-on-cf-8', 'Canyon Spectral:ON CF 8', 'mtb', 520000, 1,
     'Двухподвесный электро-MTB: мотор Shimano EP801, батарея 720 Вт·ч, ход 150/160 мм.'),
    ('specialized-stumpjumper-comp', 'Specialized Stumpjumper Comp', 'mtb', 390000, 2,
     'Трейловый двухподвес, ход 130/140 мм, карбоновая рама, SRAM GX Eagle 1x12.'),
    ('trek-marlin-7', 'Trek Marlin 7', 'mtb', 98000, 5,
     'Хардтейл с воздушной вилкой RockShox Judy, Shimano Deore 1x10, внутренняя прокладка тросов.'),
    ('scott-scale-970', 'Scott Scale 970', 'mtb', 135000, 3,
     'Кросс-кантри хардтейл, алюминиевая рама, вилка Suntour XCM 100 мм, Shimano Deore 1x12.'),
    # Гревел
    ('canyon-grizl-7', 'Canyon Grizl 7', 'grevel', 215000, 3,
     'Гревел для грунта и бездорожья: покрышки 45 мм, SRAM Apex 1x11, крепления под багаж.'),
    ('giant-revolt-2', 'Giant Revolt 2', 'grevel', 175000, 4,
     'Алюминиевый гревел с регулируемой геометрией Flip Chip, Shimano GRX 2x10.'),
    # Складные
    ('brompton-c-line-explore', 'Brompton C Line Explore', 'skladnye', 215000, 2,
     'Классический складной велосипед, колёса 16", 6 скоростей, в сложенном виде 58x56x27 см.'),
    ('shulz-krabi', 'Shulz Krabi', 'skladnye', 42000, 10,
     'Складной городской велосипед, колёса 20", стальная рама, Shimano 3 скорости, крылья и багажник.'),
    ('tern-link-b8', 'Tern Link B8', 'skladnye', 89000, 4,
     'Складной велосипед, колёса 20", 8 скоростей Shimano Claris, складывается за 10 секунд.'),
    ('dahon-mu-d9', 'Dahon Mu D9', 'skladnye', 72000, 5,
     'Лёгкий алюминиевый складной велосипед, колёса 20", 9 скоростей, вес 11 кг.'),
    # Городские
    ('giant-escape-3', 'Giant Escape 3', 'gorodskie', 56000, 7,
     'Городской фитнес-велосипед, колёса 700C, Shimano 3x8, прямой руль.'),
    ('shulz-hopper-3', 'Shulz Hopper 3', 'gorodskie', 36000, 9,
     'Городской велосипед с низкой рамой, планетарная втулка на 3 скорости, корзина и крылья.'),

    # Рамы
    ('carbon-gravel-frame-700c', 'Рама карбоновая гревел 700C', 'frame', 65000, 3,
     'Карбоновый фреймсет с вилкой: сквозные оси 12 мм, flat mount, просвет под покрышки до 45 мм.'),
    # Шины
    ('continental-grand-prix-5000-700x28', 'Continental Grand Prix 5000 700x28', 'shiny', 7900, 30,
     'Шоссейная покрышка с кордом Vectran, низкое сопротивление качению, складной корд.'),
    ('schwalbe-marathon-plus-700x38', 'Schwalbe Marathon Plus 700x38', 'shiny', 5400, 25,
     'Антипрокольная покрышка для города и туризма, слой SmartGuard 5 мм, светоотражающая полоса.'),
    ('maxxis-minion-dhf-29x25', 'Maxxis Minion DHF 29x2.5', 'shiny', 6900, 20,
     'Покрышка для эндуро и даунхилла, компаунд 3C MaxxTerra, бескамерная (TR).'),
    ('schwalbe-kojak-20x135', 'Schwalbe Kojak 20x1.35', 'shiny', 3600, 15,
     'Складная слик-покрышка для складных велосипедов с колёсами 20".'),
    # Камеры
    ('schwalbe-sv17-700c', 'Камера Schwalbe SV17 700x18-28', 'kamery', 950, 60,
     'Камера для шоссейных покрышек, ниппель Presta 40 мм.'),
    # Трансмиссия
    ('shimano-cn-hg601-11s', 'Цепь Shimano 105 CN-HG601, 11 скоростей', 'transmissiya', 3900, 25,
     'Цепь 116 звеньев с замком Quick-Link, покрытие SIL-TEC.'),
    ('shimano-cs-hg500-10s-11-34', 'Кассета Shimano CS-HG500 11-34, 10 скоростей', 'transmissiya', 4700, 18,
     'Кассета для MTB и гибридов, стандарт HG.'),
    ('sram-rival-rear-derailleur', 'Задний переключатель SRAM Rival', 'transmissiya', 14500, 6,
     'Задний переключатель для шоссе и гревела, длинная лапка, совместим с кассетами до 36T.'),
    # Тормоза
    ('shimano-deore-br-m6100', 'Тормоза Shimano Deore BR-M6100', 'tormoza', 9800, 12,
     'Гидравлический дисковый тормоз, двухпоршневой калипер, ручка I-Spec EV.'),
    # Педали
    ('shimano-pd-m520', 'Педали Shimano PD-M520 SPD', 'pedali', 4300, 20,
     'Контактные педали SPD, двусторонние, шипы SM-SH51 в комплекте.'),
    # Сёдла
    ('terry-fly-arteria', 'Седло Terry Fly Arteria', 'sedla', 7500, 10,
     'Спортивное седло с анатомическим вырезом, рельсы Cr-Mo.'),

    # Аксессуары
    ('busch-muller-lumotec-iq', 'Фара Busch+Müller Lumotec IQ', 'fonari', 3800, 14,
     'Передняя фара под динамо-втулку, 60 люкс, встроенный отражатель.'),
    ('helmet-road-mips', 'Шлем шоссейный MIPS', 'shlemy', 9500, 15,
     'Лёгкий вентилируемый шлем с системой MIPS, регулировка обхвата, размеры S–L.'),
    ('abus-granit-x-plus-540', 'Замок ABUS Granit X-Plus 540', 'zamki', 12500, 10,
     'U-образный замок, дужка 13 мм из закалённой стали, уровень защиты 15/15.'),
    ('topeak-joeblow-sport-3', 'Насос Topeak JoeBlow Sport III', 'nasosy', 5200, 12,
     'Напольный насос с манометром, до 11 бар, головка под Presta и Schrader.'),
    ('garmin-edge-540', 'Велокомпьютер Garmin Edge 540', 'velokompyutery', 39000, 5,
     'GPS-велокомпьютер с картами, мультидиапазонный GNSS, подсказки по подъёмам ClimbPro.'),
    ('elite-custom-race-cage', 'Флягодержатель Elite Custom Race', 'flyagoderzhateli', 1500, 40,
     'Пластиковый флягодержатель, 32 г, надёжно держит флягу на неровностях.'),
]


class Command(BaseCommand):
    help = 'Заполняет dev-базу тестовыми категориями и товарами (велосипеды, запчасти, аксессуары).'

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        for slug, name, parent_slug in CATEGORIES:
            categories[slug], _ = Category.objects.update_or_create(
                slug=slug,
                defaults={'name': name, 'parent': categories.get(parent_slug)},
            )

        created = 0
        for slug, name, category_slug, price, stock, description in PRODUCTS:
            product, is_new = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': categories[category_slug],
                    'price': Decimal(price),
                    'stock': stock,
                    'description': description,
                    'is_active': True,
                },
            )
            # картинку кладём только один раз, чтобы повторный запуск не плодил файлы в media
            if not product.image:
                with open(IMAGES_DIR / f'{slug}.jpg', 'rb') as f:
                    product.image.save(f'{slug}.jpg', File(f), save=True)
            created += is_new

        self.stdout.write(self.style.SUCCESS(
            f'Категорий: {len(CATEGORIES)}, товаров: {len(PRODUCTS)} (новых {created}).'
        ))
