/*!
 * Lunr languages, `Sanskrit` language
 * https://github.com/MiKr13/lunr-languages
 *
 * Copyright 2023, India
 * http://www.mozilla.org/MPL/
 */
/*!
 * based on
 * Snowball JavaScript Library v0.3
 * http://code.google.com/p/urim/
 * http://snowball.tartarus.org/
 *
 * Copyright 2010, Oleg Mazko
 * http://www.mozilla.org/MPL/
 */

/**
 * export the module via AMD, CommonJS or as a browser global
 * Export code from https://github.com/umdjs/umd/blob/master/returnExports.js
 */
;
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD. Register as an anonymous module.
    define(factory)
  } else if (typeof exports === 'object') {
    /**
     * Node. Does not work with strict CommonJS, but
     * only CommonJS-like environments that support module.exports,
     * like Node.
     */
    module.exports = factory()
  } else {
    // Browser globals (root is window)
    factory()(root.lunr);
  }
}(this, function() {
  /**
   * Just return a value to define the module export.
   * This example returns an object, but the module
   * can return a function as the exported value.
   */
  return function(lunr) {
    /* throw error if lunr is not yet included */
    if ('undefined' === typeof lunr) {
      throw new Error('Lunr is not present. Please include / require Lunr before this script.');
    }

    /* throw error if lunr stemmer support is not yet included */
    if ('undefined' === typeof lunr.stemmerSupport) {
      throw new Error('Lunr stemmer support is not present. Please include / require Lunr stemmer support before this script.');
    }

    /* register specific locale function */
    lunr.sa = function() {
      this.pipeline.reset();
      this.pipeline.add(
        lunr.sa.trimmer,
        lunr.sa.stopWordFilter,
        lunr.sa.stemmer
      );

      if (this.searchPipeline) {
        this.searchPipeline.reset();
        this.searchPipeline.add(lunr.sa.stemmer)
      }
    };

    /* lunr trimmer function */
    lunr.sa.wordCharacters = "\u0900-\u0903\u0904-\u090f\u0910-\u091f\u0920-\u092f\u0930-\u093f\u0940-\u094f\u0950-\u095f\u0960-\u096f\u0970-\u097f\uA8E0-\uA8F1\uA8F2-\uA8F7\uA8F8-\uA8FB\uA8FC-\uA8FD\uA8FE-\uA8FF\u11B00-\u11B09";
    lunr.sa.trimmer = lunr.trimmerSupport.generateTrimmer(lunr.sa.wordCharacters);

    lunr.Pipeline.registerFunction(lunr.sa.trimmer, 'trimmer-sa');
    /* lunr stop word filter */
    lunr.sa.stopWordFilter = lunr.generateStopWordFilter(
      'तथा अयम्‌ एकम्‌ इत्यस्मिन्‌ तथा तत्‌ वा अयम्‌ इत्यस्य ते आहूत उपरि तेषाम्‌  किन्तु तेषाम्‌ तदा इत्यनेन अधिकः इत्यस्य तत्‌ केचन बहवः द्वि तथा महत्वपूर्णः अयम्‌ अस्य  विषये अयं अस्ति तत्‌ प्रथमः विषये इत्युपरि इत्युपरि इतर अधिकतमः अधिकः अपि सामान्यतया ठ इतरेतर नूतनम्‌ द  न्यूनम्‌ कश्चित्‌ वा विशालः द  सः अस्ति तदनुसारम् तत्र अस्ति केवलम्‌ अपि अत्र सर्वे विविधाः तत्‌ बहवः यतः इदानीम्‌ द  दक्षिण इत्यस्मै तस्य उपरि नथ अतीव कार्यम्‌ सर्वे एकैकम्‌ इत्यादि। एते सन्ति  उत इत्थम्‌ मध्ये एतदर्थं . स कस्य प्रथमः श्री. करोति अस्मिन् प्रकारः निर्मिता कालः तत्र कर्तुं  समान अधुना ते सन्ति स एकः अस्ति सः अर्थात् तेषां कृते . स्थितम्  विशेषः अग्रिम तेषाम्‌ समान स्रोतः ख म समान इदानीमपि अधिकतया करोतु ते समान इत्यस्य वीथी सह यस्मिन्  कृतवान्‌ धृतः तदा पुनः पूर्वं सः आगतः किम्‌ कुल इतर पुरा  मात्रा स विषये उ अतएव अपि नगरस्य  उपरि यतः प्रतिशतं  कतरः कालः साधनानि भूत तथापि जात सम्बन्धि अन्यत्‌ ग अतः अस्माकं स्वकीयाः अस्माकं इदानीं अन्तः इत्यादयः भवन्तः इत्यादयः एते एताः तस्य अस्य इदम् एते तेषां तेषां तेषां तान् तेषां तेषां तेषां समानः सः एकः च तादृशाः बहवः अन्ये च वदन्ति यत् कियत् कस्मै  कस्मै  यस्मै  यस्मै  यस्मै  यस्मै न अतिनीचः किन्तु प्रथमं सम्पूर्णतया  ततः चिरकालानन्तरं पुस्तकं सम्पूर्णतया अन्तः  किन्तु अत्र वा इह इव श्रद्धाय अवशिष्यते  परन्तु अन्ये वर्गाः सन्ति ते सन्ति शक्नुवन्ति सर्वे मिलित्वा सर्वे एकत्र"'.split(' '));
    /* lunr stemmer function */
    lunr.sa.stemmer = (function() {

      return function(word) {
        // for lunr version 2
        if (typeof word.update === "function") {
          return word.update(function(word) {
            return word;
          })
        } else { // for lunr version <= 1
          return word;
        }

      }
    })();

    var segmenter = lunr.wordcut;
    segmenter.init();
    lunr.sa.tokenizer = function(obj) {
      if (!arguments.length || obj == null || obj == undefined) return []
      if (Array.isArray(obj)) return obj.map(function(t) {
        return isLunr2 ? new lunr.Token(t.toLowerCase()) : t.toLowerCase()
      });

      var str = obj.toString().toLowerCase().replace(/^\s+/, '');
      return segmenter.cut(str).split('|');
    }

    lunr.Pipeline.registerFunction(lunr.sa.stemmer, 'stemmer-sa');
    lunr.Pipeline.registerFunction(lunr.sa.stopWordFilter, 'stopWordFilter-sa');

  };
}))