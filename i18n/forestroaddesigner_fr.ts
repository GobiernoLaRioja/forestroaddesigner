<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.0" language="fr_FR">
<context>
    <name>AboutDialog</name>
    <message>
        <location filename="../dlgabout.ui" line="20"/>
        <source>Forest Road Designer About</source>
        <translation>A propos de Forest Road Designer</translation>
    </message>
    <message>
        <location filename="../dlgabout.ui" line="30"/>
        <source>FOREST ROAD DESIGNER PLUGIN</source>
        <translation>EXTENSION FOREST ROAD DESIGNER</translation>
    </message>
    <message>
        <location filename="../dlgabout.ui" line="113"/>
        <source>PANOimagen S.L.</source>
        <translation>PANOimagen S.L.</translation>
    </message>
</context>
<context>
    <name>ForestRoadDesignerDockWidgetBase</name>
    <message>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="38"/>
        <source>Forest Road Designer</source>
        <translation>Forest Road Designer</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="76"/>
        <source>Capa ráster del Modelo Digital del Terreno (DTM)</source>
        <translation>Couche Raster Modele Numérique de Terrain (MNT)</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="89"/>
        <source>Especifique el Modelo Digital del Terreno que contiene la zona de interés, en formato raster</source>
        <translation>Précisez le modèle numérique de terrain qui contient la zone d'intérêt, au format raster</translation>
    </message>
    <message>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="106"/>
        <source>Directorio de salida</source>
        <translation>Dossier de sortie</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="121"/>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="128"/>
        <source>Especifique el directorio dónde se guardarán los resultados</source>
        <translation>Précisez le dossier en sortie pour stocker les résultats </translation>
    </message>
    <message>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="131"/>
        <source>...</source>
        <translation>...</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="156"/>
        <source>Especifique los parámetros de diseño </source>
        <translation>Précisez les paramètres de construction</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="159"/>
        <source>Parámetros de diseño</source>
        <translation>Paramètres de construction</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="177"/>
        <source>Se inspecciona una vecindad de tamaño (2 · N + 1) x (2 · N + 1) en cada punto del recorrido para encontrar el camino óptimo</source>
        <translation>Une fenêtre contextuelle de (2 · N + 1) x (2 · N + 1) pixel est inspecté à chaque point pour trouver le chemin optimal</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="180"/>
        <source>Tamaño vecindad</source>
        <translation>Fenêtre contextuelle d'analyse</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="193"/>
        <source>Área de búsquda del camino óptimo (en metros)</source>
        <translation>Zone de recherche du chemin optimal en mètre</translation>
    </message>
    <message>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="196"/>
        <source>(- x -)</source>
        <translation>(- x -)</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="226"/>
        <source>Especifique el factor de vecindad. Número de píxeles del modelo digital del terreno sobre los que se busca la ruta óptima. A mayor valor el área de búsqueda es mayor.</source>
        <translation>Précisez le facteur de voisinage. Plus la valeur est élevé, plus la zone de recherche est grande</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="258"/>
        <source>Especifique la penalización por cambios de dirección. A mayor valor se evitará el trazado con curvas cerradas.</source>
        <translation>Précisez la pénalité pour les changements de direction. Plus la valeur est élevée, moins le tracé sera sinueux.</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="261"/>
        <source>Penalización por cambio de dirección</source>
        <translation>Pénalité de changement de direction</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="286"/>
        <source>Especifique el valor de la penalización para los cambios de dirección. Cada giro de 180º en el trazado penaliza el camino con el valor especificado.</source>
        <translation>Précisez la pénalité pour les changements de direction.</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="295"/>
        <source> m/180º</source>
        <translation>m/180º</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="324"/>
        <source>Especifique la penalización por cambios de rasante. A mayor valor se evitará el trazado con cambios de rasante.</source>
        <translation>Précisez la pénalité pour une inversion de pente. Une valeur forte tend à éviter de croiser les isolignes.</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="327"/>
        <source>Penalización por cambio de rasante</source>
        <translation>Pénalité pour les inversions de pente</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="352"/>
        <source>Especifique el valor de la penalización para los cambios de rasante. Cada cambio de pendiente máximo (de -pte_max a +pte_max) se penaliza con el valor especificado.</source>
        <translation>Précisez la pénalité pour une inversion de pente.</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="358"/>
        <source> m/cambio máximo pendiente</source>
        <translation>m/changement de pente</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="391"/>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="431"/>
        <source>Especifique el factor de tolerancia para la polilínea de resultado. A menor valor la polilínea final se ajustará a los puntos de la ruta óptima.</source>
        <translation>Précisez le facteur de tolérance pour la simplification de la polyligne. Une valeur faible n'utilisera que les points bruts obtenus</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="394"/>
        <source>Tolerancia de la polilínea de resultado</source>
        <translation>Tolérance pour le tracé de la polyligne</translation>
    </message>
    <message>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="401"/>
        <source>(-)</source>
        <translation>(-)</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="468"/>
        <source>Pendiente mínima admisible</source>
        <translation>Pente minimale admise</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="487"/>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="563"/>
        <source>--º</source>
        <translation>--º</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="512"/>
        <source>Especifique el valor de pendiente mínima admisible para el diseño del trazado</source>
        <translation>Précisez la valeur de pente minimale admise pour la construction du tracé</translation>
    </message>
    <message>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="518"/>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="597"/>
        <source>%</source>
        <translation>%</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="544"/>
        <source>Pendiente máxima admisible</source>
        <translation>Pente maximale admise</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="591"/>
        <source>Especifique el valor de pendiente máxima admisible para el diseño del trazado</source>
        <translation>Précisez la valeur de pente maximale admise pour la construction du tracé</translation>
    </message>
    <message>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="662"/>
        <source>Gobierno de La Rioja</source>
        <translation>Gobierno de La Rioja</translation>
    </message>
    <message>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="690"/>
        <source>PANOimagen S.L.</source>
        <translation>PANOimagen S.L.</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="722"/>
        <source>Versión de Forest Road Designer</source>
        <translation>Version de Forest Road Designer</translation>
    </message>
    <message>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="725"/>
        <source>Forest Road Designer version -.-</source>
        <translation>Forest Road Designer version -.-</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="748"/>
        <source>Active la casilla si desea realizar el diseño con zonas a excluir del trazado</source>
        <translation>Cochez la case pour préciser des zones à exclure</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="751"/>
        <source>Diseño con zonas excluidas para el trazado</source>
        <translation>Zones à exclure du tracé</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="773"/>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="792"/>
        <source>Especifique la capa vectorial que incluye las zonas a excluir del diseño del trazado</source>
        <translation>Précisez la couche vectoriel qui contient les zones à exclure de la recherche de tracé</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="776"/>
        <source>Capa de exclusión para el trazado </source>
        <translation>Couche de zones interdites au tracé</translation>
    </message>
    <message>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="806"/>
        <source>Habilitar el proceso por lotes</source>
        <translation>Activer le traitement par lots</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="824"/>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="843"/>
        <source>Especifique la capa vectorial (polilínea) que contiene el punto de inicio, puntos de paso (opcionales) y punto de llegada, en formato vectorial (ESRI Shapefile)</source>
        <translation>Précisez la couche vectoriel (polyligne) qui contient les points de début, points de passage (optionnel) et points de fin</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="827"/>
        <source>Capa vectorial de entrada con los puntos de paso (polilínea)</source>
        <translation>Couche vectoriel des points de passages (polyligne)</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="860"/>
        <source>Comenzar el diseño en modo interactivo</source>
        <translation>Commencer le tracé en mode interactif</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="863"/>
        <source>Iniciar el proceso de diseño</source>
        <translation>Commencer le processus de tracé</translation>
    </message>
    <message>
        <location filename="../forest_road_designer_dockwidget_base.ui" line="876"/>
        <source>Terminar el proceso interactivo</source>
        <translation>Terminer le tracé</translation>
    </message>
    <message utf8="true">
        <location filename="../forest_road_designer_dockwidget_base.ui" line="879"/>
        <source>Finalizar captura -&gt; simplificación polilinea</source>
        <translation>Finir le tracé => conversion en polyligne</translation>
    </message>
</context>
</TS>
