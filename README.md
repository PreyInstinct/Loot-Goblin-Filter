# Loot Goblin PD2 Loot-Filter

This filter is forked from [Kryszard's PD2 Loot Filter](https://github.com/Kryszard-POD/Kryszard-s-PD2-Loot-Filter). Please see the documentation there regarding filter levels and other features not described here. Thank you, Kryszard, for all your good work.

# About

This filter is still very much a work in progress. Some features may not be fully polished, and vestiges of obsolete features may linger.

## Points

The main feature this filter introduces is a visual point-based system for some item types (and hopefully most magic/rare types in the future.) This feature is designed to help you quickly sort out loot that might have some use or value from Charsi food. It is not intended to accurately assess the value of items or call out GG gear, but merely to signal if the full item description is even worth looking at.

A point represents a well rolled affix - either a rare/highly sought after affix, a high roll on a desireable affix, or both. Not all points are equal, though I try to weight the most desireable affixes higher by making them worth multiple points, nor are points equivalent between item classes. The gray row of points shows you the maximum possible number of points (not including corruptions) for an item of a given type.

Points are color coded by their broad utility class. Since you are usually trying to min-max your build, lots of the same or similar colored points will probably be better than "rainbow" arrays, but if something has a lot of points of any color on it you should probably take a look and assess for yourself.

|Category           |Color      |Description                        |
|-------------------|-----------|-----------------------------------|
|Skills             |Gold       |Includes +% elemental damage       |
|Speed              |Yellow     |IAS, FHR, FCR, FBR                 |
|Physical Damage    |Red        |% ED and flat min/max              |
|Damage Effects     |Coral      |CB, DS, wounds, etc                |
|Elemental Damage   |Orange     |Flat elemental/magic damage        |
|Magic Protection   |Purple     |Resistances & Magic Damage Reduced |
|HP/MP              |Blue       |HP/MP, LL/ML, LaeK/MaeK            |
|Physical Protection|Teal       |Defense, Block, & PDR              |
|Statistics         |Dark Green |Str, Dex, Vit, Ene                 |
|Other              |Sage       |AR, pierce, tele charges, etc      |

Point systems are currently implemented for:
 - Charms
 - Quivers
 - Jewels
 - Rings
 - Amulets
 - Rare Gloves
 - Rare Belts
 - Rare Boots
 - Rare Chests

## Magic Item Callouts

Some magic items with useful affix combinations have their names completely changed and colored to draw attention to them. This is similar to Kryszard's "Shop Hunting" tips, but puts the information right at the top. Right now my approach is a little bespoke depending on the item type, so I may unify the style in the future. It should be easy to spot the following, though:
 - +3 skill gloves (w & w/o IAS)
 - +3 skill amulets (w & w/o good combo affixes)
 - Allres & FCR/DMG magic rings

## Skill Tags (Pointmods)

While generally very good, I have re-worked Kryszard's pointmod tags to suit my preference. In general, my aims have been to 1) improve legibility, 2) show more information while using as litte additional space as possible, and 3) extend the usefulness of this feature to magic, rare, and crafted item hunting in addition to picking bases.

### Inclusion of Skill Trees

Class-focused items don't have all +ALLSK, +CLSK (e.g. Paladin Skills), or +TABSK (e.g. Combat Skills) automods, with the exception of Amazon bows, which don't have +SK (single skill) automods, so there is no need to worry about these mods when hunting for bases. However, magic and rare items that combine +TABSK and +SK can be quite useful. Kryszard's approach to these is to add a "+High Skill Roll" tag on these items, which is quite reasonable considering these mods can't be seen until IDed. I like having this information in a consistent place (the name line), though, so I've opted to include them.

### New Skill Abbreviations
I personally find the three letter skill abbreviations a bit obtuse. I think there are just too many skills, with many of them having very similar names, for a three letter system to be legible. I have thus implemented a slightly more complex, but hopefully more legible and intuitive system.
 - All Skills is ALL(caps).
 - Acronyms are also in ALLCAPS. E.g. SS (Shape Shifting), BO (Battle Orders), CDM (Claw & Dagger Mastery), ES (Energy Shield).
 - Bonuses to skill trees (including CLSK and TABSK) use Proper Capitalization E.g. Cries, Cold, JvSp, Mast.
 - Single skill bonuses (that aren't acronyms) use camelCaps. E.g. fOrb, maul, zerk, bFury.
 - Where possible, skills that have common words in the same tree are shortened as much as possible and always in the same way. E.g. Assasin "Dragon" skills are dTal, dClaw, dTail, and dFlt, while Amazon "Arrow" skills are magA, firA, colA, expA, iceA, gudA, immA, and frzA, and "Strike" skills are powA, chgS, litS, tigS, cbrS, PhoS, psnS.
 - Some simple skills are named after their primary affect, rather than the actual skill name. E.g. +def, +hp, +spd, +res, and bleed for Barb masteries, and +AR for Amazon's Penetrate.

See All.skills for the full list of abbreviations.

### Color Coding

Skill bonuses use the D2 rarity colors: +1 is rendered blue, +2 is rendered yellow, and +3 is rendered gold.

Simlarly, the skills themselves use the D2 rarity colors: single skills are white, skill tabs are blue, class skills are yellow, and all skills is gold.

Last, the braces themselves use the same rarity colors to denote potentially desirable combos.

First, I categorized the skills into a few types - most importantly "primary" skills, which are those skills that some build is likely to spam or try to maximize. You can see all the categorizations in All.skills. My knowledge is not encyclopedic, and I welcome suggestions for recategorization.

For non-magic items (i.e. class-focused bases), the bonus to a primary skill and the total value of pointmods determines the color of the {braces}.
 - Gray: The item only has bonuses to non-primary skills, even if those bonuses are large.
 - White: +1-+2 in a primary skill.
 - Blue: +3 in a primary skill and a total of +3-5.
 - Yellow: +3 in a primary skill and a total of +6-7.
 - Gold: +3 in a primary skill and a total of +7-8.

Next, the highest total bonus to a primary skill determines the color of the {braces}.
 - Gray: The item only has bonuses to non-primary skills, even if those bonuses are large.
 - White: +1-2 in a primary skill.
 - Blue: +3 in a primary skill.
 - Yellow: +4 in a primary skill.
 - Gold: +5 or greater in a primary skill.

### +High Skills Roll

For the time being, I left Kryszard's colorful tag in, though at some point in the future I may replace this with more nuanced tags.

