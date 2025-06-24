import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0) #初期の向き（左）

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0] #各方向の合計移動（初期は静止）
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv) #移動実行
        if check_bound(self.rct) != (True, True): #画面外なら戻す
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv) #向きを更新
            self.img = __class__.imgs[self.dire] #向きに応じた画像に変更
        screen.blit(self.img, self.rct) #描画


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img0 = pg.image.load("fig/beam.png")
        self.vx, self.vy = bird.dire  # 向きに応じた速度

        # ビームの向きに応じて回転
        angle_rad = math.atan2(-self.vy, self.vx)  # -vyにするのがPygameの座標系
        angle_deg = math.degrees(angle_rad)
        self.img = pg.transform.rotozoom(self.img0, angle_deg, 1.0)

        self.rct = self.img.get_rect()

        # 向きに応じて初期位置調整
        bw, bh = bird.rct.width, bird.rct.height
        bx, by = bird.rct.center
        self.rct.centerx = bx + bw * self.vx / 5
        self.rct.centery = by + bh * self.vy / 5

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rct.move_ip(self.vx, self.vy)
        if check_bound(self.rct) == (True, True):
            screen.blit(self.img, self.rct)    


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

class Score:
    """
    スコアに関するクラス
    """
    def __init__(self):
        """
        スコア表示用のフォント・色・初期スコアの設定
        引数：なし
        戻り値：なし
        """
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.fonto.render(f"スコア:{self.score}", True, self.color)
        self.rct = (100, HEIGHT - 50)

    def update(self, screen:pg.Surface):
        """
        現在のスコアを表示
        引数screen：画面Surface
        戻り値：なし
        """
        self.img = self.fonto.render(f"スコア:{self.score}", True, self.color)
        screen.blit(self.img, self.rct)
    
    def increment(self, point = 1):
        self.score += point

class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, center: tuple[int, int]):
        """
        引数に基づき爆発エフェクトを生成する関数
        引数center：爆発エフェクトの中心座標タプル
        戻り値：なし
        """
        self.surfaces = [
            pg.image.load("fig/explosion.gif").convert_alpha(),
            pg.transform.flip(pg.image.load("fig/explosion.gif").convert_alpha(), True, False),
        ]
        self.index = 0
        self.rct = self.surfaces[0].get_rect()
        self.rct.center = center
        self.life = 10  # 爆発の表示時間（フレーム数）

    def update(self, screen: pg.Surface):
        """
        爆発エフェクトを画面に描画する関数
        引数screen：画面Surface
        戻り値：なし
        """
        if self.life > 0:
            # 爆発画像を交互に切り替え
            self.index = (self.index + 1) % 2
            screen.blit(self.surfaces[self.index], self.rct)
            self.life -= 1

def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    score = Score()
    

    # bomb = Bomb((255, 0, 0), 10)
    # bombs= []
    # for _ in range(NUM_OF_BOMBS):
    #     bombs.append(Bomb((255, 0, 0), 10))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)] 
    beams = []  # 複数ビームに対応
    explosions = [] #爆発エフェク用リスト
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beams.append(Beam(bird))            
        screen.blit(bg_img, [0, 0])
        
        # if bomb is not None:
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return
            
        # if bomb is not None:
        for beam in beams:
            for i, bomb in enumerate(bombs):
                if bomb is not None and beam.rct.colliderect(bomb.rct):
                    explosions.append(Explosion(bomb.rct.center))
                    beams[beams.index(beam)] = None
                    bombs[i] = None
                    bird.change_img(6, screen)
                    score.increment()
                    break
        bombs = [bomb for bomb in bombs if bomb is not None]
        explosions = [exp for exp in explosions if exp.life > 0]
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        new_beams = []
        for beam in beams:         
            if beam is not None and check_bound(beam.rct) == (True, True):
                beam.update(screen)
                new_beams.append(beam)
        beams = new_beams

        for exp in explosions:
            exp.update(screen)
        
        for bomb in bombs:
            bomb.update(screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
