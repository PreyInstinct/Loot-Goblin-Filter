# Loot Goblin PD2 Loot-Filter

This filter is forked from [Kryszard's PD2 Loot Filter](https://github.com/Kryszard-POD/Kryszard-s-PD2-Loot-Filter). Please see the documentation there regarding filter levels and other features not described here. Thank you, Kryszard, for all your good work.

# About

This filter is still very much a work in progress. Some features may not be fully polished, and vestiges of obsolete features may linger.

## Points

The main feature this filter introduces is a visual point-based system for some item types (and hopefully most magic/rare types in the future.) This feature is designed to help you quickly sort out loot that might have some use or value from Charsi food. It is not intended to accurately assess the value of items or call out GG gear, but merely to signal if the full item description is even worth looking at.

A point represents a well rolled affix - either a rare/highly sought after affix, a high roll on a desireable affix, or both. Not all points are equal, though I try to weight the most desireable affixes higher by making them worth multiple points, nor are points equivalent between item classes. The gray row of points shows you the maximum possible number of points (not including corruptions) for an item of a given type.

Points are color coded by their broad utility class. Since you are usually trying to min-max your build, lots of the same or similar colored points will probably be better than "rainbow" arrays, but if something has a lot of points of any color on it you should probably take a look and assess for yourself.

|Category           |Color      |Description                   |
|-------------------|-----------|------------------------------|
|Skills             |Gold       |Includes +% elemental damage  |
|Speed              |Yellow     |IAS, FHR, FCR, FBR            |
|Physical Damage    |Red        |% ED and flat min/max         |
|Elemental Damage   |Orange     |Flat elemental/magic damage   |
|Damage Effects     |Coral      |CB, DS, wounds, etc           |
|Damage Reduction   |Purple     |Includes resistances & PDR    |
|HP/MP              |Blue       |HP/MP, LL/ML, LaeK/MaeK       |
|Abilities          |Dark Green |Str, Dex, Vit, Ene            |
|Utility            |Teal       |Pierce, tele charges, etc     |
|Other              |Sage       |                              |

## Skill Tags

I personally find Kryszard's three letter skill abbreviations a bit obtuse. I think there are just too many skills, with many of them having very similar names, for a three letter system to be legible. I have thus replaced them with my own abbreviations using camelCase for single skills and ALLCAPS for skill trees, class skills, and all skills. It takes up more space, but I hope you find it easier to find the class items you're hunting for.