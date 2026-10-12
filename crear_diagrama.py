from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / 'diagrama_secuencia.png'
W, H = 2400, 2910
im = Image.new('RGB', (W, H), '#f8fafc')
d = ImageDraw.Draw(im)
fonts = Path('C:/Windows/Fonts')
def font(size, bold=False):
    return ImageFont.truetype(str(fonts / ('arialbd.ttf' if bold else 'arial.ttf')), size)
def center(text, x, y, size=29, color='#17263c', bold=False):
    d.multiline_text((x, y), text, font=font(size, bold), fill=color, anchor='mm', align='center', spacing=9)

d.rectangle((0, 0, W, 160), fill='#13243b')
center('MARCADOR EN VIVO', W/2, 58, 48, 'white', True)
center('Diagrama de secuencia · Inicio de sesión y consulta de datos', W/2, 118, 31, '#cbd5e1')
xs = [180, 670, 1100, 1580, 2180]
names = ['Usuario', 'Frontend externo', 'sessionStorage', 'API Django', 'Base de datos']
for x, name in zip(xs, names):
    d.rounded_rectangle((x-165, 190, x+165, 272), radius=15, fill='#e1ebf7', outline='#b6c8de', width=2)
    center(name, x, 231, 30, bold=True)
    for y in range(284, 2790, 20):
        d.line((x,y,x,y+10), fill='#b4c2d3', width=3)

def phase(y, label):
    d.rounded_rectangle((40,y-27,W-40,y+27), radius=9, fill='#dce9f5')
    center(label, W/2, y, 29, '#163d63', True)

def arrow(a,b,y,label,response=False):
    x1,x2=xs[a],xs[b]
    color='#16726b' if response else '#235d9c'
    if response:
        direction=1 if x2>x1 else -1
        for t in range(0,abs(x2-x1),22):
            start=x1+direction*t
            end=x1+direction*min(t+12,abs(x2-x1))
            d.line((start,y,end,y),fill=color,width=4)
    else:
        d.line((x1,y,x2,y),fill=color,width=4)
    direction=1 if x2>x1 else -1
    d.polygon([(x2,y),(x2-direction*17,y-10),(x2-direction*17,y+10)],fill=color)
    f=font(27)
    box=d.multiline_textbbox((0,0),label,font=f,spacing=7)
    tw,th=box[2]-box[0],box[3]-box[1]
    cx=(x1+x2)/2
    d.rounded_rectangle((cx-tw/2-12,y-th-24,cx+tw/2+12,y-10),radius=6,fill='#f8fafc')
    center(label,cx,y-th/2-17,27,color)

phase(335,'1. Inicio de sesión y consulta del rol')
arrow(0,1,425,'Ingresa usuario y contraseña')
arrow(1,3,535,'POST /api/token/\nJSON: username, password')
arrow(3,4,645,'Consulta usuario\ny valida credenciales')
arrow(4,3,735,'Usuario válido',True)
arrow(3,1,835,'200 OK · JSON: access, refresh',True)
arrow(1,2,935,'Guarda access\ny refresh')
arrow(1,3,1045,'GET /api/me/\nAuthorization: Bearer access')
arrow(3,4,1145,'Tras verificar JWT,\nconsulta usuario y rol')
arrow(4,3,1240,'Datos del usuario',True)
arrow(3,1,1340,'200 OK · JSON: id, username, rol',True)
arrow(1,0,1430,'Muestra usuario, rol y controles',True)
phase(1510,'2. Consulta de partidos en juego')
arrow(0,1,1600,'Selecciona filtro «En juego»')
arrow(2,1,1695,'Lee access guardado',True)
arrow(1,3,1810,'GET /api/partidos/?liga={id}&estado=en_juego\nAuthorization: Bearer access')
arrow(3,4,1910,'Consulta partidos filtrados')
arrow(4,3,2000,'Partidos de la liga en juego',True)
arrow(3,1,2090,'200 OK · JSON paginado: results',True)
arrow(1,0,2180,'Muestra nombres, goles y estado',True)
phase(2260,'3. Tabla de posiciones al cargar la liga')
arrow(1,3,2370,'GET /api/ligas/{id}/tabla/')
arrow(3,4,2470,'Consulta equipos y\npartidos finalizados')
arrow(4,3,2570,'Datos para calcular posiciones',True)
arrow(3,1,2690,'Calcula estadísticas y puntos\n200 OK · Lista JSON de posiciones',True)
arrow(1,0,2790,'Muestra tabla de posiciones',True)
center('Flecha continua: petición / acción     ·     Flecha discontinua: respuesta / datos',W/2,2870,26,'#53657b')
im.save(OUT)
print(OUT)
