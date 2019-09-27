#Librerias importantes
import time
import redis
#Variable para llamar las funciones de redis
conn = redis.Redis(host='localhost', port=6379, db=0)

#Prepara nuestras constantes.
ONE_WEEK_IN_SECONDS = 7 * 86400
VOTE_SCORE = 432


#Funcion para votar un articulo
def article_vote(conn, user, article): 
    #Se pide: conn que representa las funciones de redis, user que es la clave de usuario, article que es la clave del articulo
    
    
    #Calcule el tiempo límite para votar.
    #Los articulos solo se pueden votar una semana despues de ser publicados
    cutoff = time.time() - ONE_WEEK_IN_SECONDS

    #Verifique si aún se puede votar el artículo, si el valor de cotoff es mayor que la fecha de publicacion termina la funcion dado 
    #que no se puede votar para ese articulo, si la fecha de articulo es menor es porque aun no se ha cumplido una semana de su publicacion
    if conn.zscore('time:', article) < cutoff:
        return

     # Toma el id de la llave articulo
    article_id = article.partition(':')[-1]

    #Si el usuario no ha votado antes por este artículo, incremente la
    #  puntuación del artículo y el recuento de votos.
    if conn.sadd('voted:' + article_id, user):
        #LA funcion zincrby (Para zset) incrementa el puntaje (score) del articulo en la clave score:
        conn.zincrby('score:', article, VOTE_SCORE)
        #hincrby es una funcuon similar a zincrby para Hash
        conn.hincrby(article, 'votes', 1)

#Función para crear un articulo
def new_article(conn, user, title, link):
    article_id = str(conn.incr('article:')) #Genera un nuevo id de articulo(ademas de crear article si no está creado)
    voted = 'voted:' + article_id  #Crea la clave voted con el id del articulo publicado, el primer voto es de quien lo hizo
    conn.sadd(voted, user) #Agrega en voted a user representando que el usuario votó por el articulo
    conn.expire(voted, ONE_WEEK_IN_SECONDS) #Configura para que el voto del articulo caduque en una semana
    now = time.time()  #Optiene la hora en ese momento
    #crea el articulo hash.
    article = 'article:' + article_id #Genera la clave  Articulo con el id del articulo
    conn.hmset(article, {
        'title': title,
        'link': link,
        'poster': user,
        'time': now,
        'votes': 1,
    })
    #Agregue el artículo al tiempo y califique los ZSET ordenados.
    conn.zadd('score:', {article: now + VOTE_SCORE}) #Representa la puntuacion del articulo
    conn.zadd('time:', {article: now}) #representa la fecha de publicacion del articulo
    return article_id #Como respuesta de la operacion regresa la clave del articulo

#Funcion de creación del Usuario
def new_user(conn, name, email):
    user_id = email #usaremos el email como id unico, dado de que no puede haber diferentes usuarios con el mismo correo
    register = "user:"
    user = "user:" + user_id

    if conn.sadd(register, "user:" + user_id):
        print("Registrado\n")
        conn.hmset(user, {
        'name': name,
        'email': email,
        })
        
        return user_id
    else:
        print("Usuario ya existe")
        return user_id

#Regresa la cantidad de articulos de manera descendente que le pidamos
def get_articles(conn, mostrar, order='score:'):

    #empieza desde el primer articulo
    start = 0
    # finaliza despues de la cantidad de articulos que le dijimos que muestre
    end = start + mostrar - 1
    # En ids se guarda de manera ordenada, dado que los zset guardan los datos de manera ascendente es necesariop aplicar zrevrange ara que nos 
    #muestre los datos de manera descendente
    ids = conn.zrevrange(order, start, end)
    #crea la lista donde se guardará la información de los articulos
    articles = []
    #crea un ciclo en el cual in tomará el valor de cada valor en ids(o sea article:1,article:2,...,etc)
    for id in ids:
        #guardará toda la informacion en article_data 
        article_data = conn.hgetall(id)
        #registra el id en article_data[] con su mismo nombre
        article_data['id'] = id
        #agrega la informacion de cada id 
        articles.append(article_data)  
        #Regresa la lista con toda la info de cada articulo del ranking
    return articles

