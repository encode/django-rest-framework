/*!
 * Lunr languages, `Hindi` language
 * https://github.com/MiKr13/lunr-languages
 *
 * Copyright 2020, Mihir Kumar
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
    lunr.hi = function() {
      this.pipeline.reset();
      this.pipeline.add(
        lunr.hi.trimmer,
        lunr.hi.stopWordFilter,
        lunr.hi.stemmer
      );

      // change the tokenizer for japanese one
      // if (isLunr2) { // for lunr version 2.0.0
      //   this.tokenizer = lunr.hi.tokenizer;
      // } else {
      //   if (lunr.tokenizer) { // for lunr version 0.6.0
      //     lunr.tokenizer = lunr.hi.tokenizer;
      //   }
      //   if (this.tokenizerFn) { // for lunr version 0.7.0 -> 1.0.0
      //     this.tokenizerFn = lunr.hi.tokenizer;
      //   }
      // }

      if (this.searchPipeline) {
        this.searchPipeline.reset();
        this.searchPipeline.add(lunr.hi.stemmer)
      }
    };

    /* lunr trimmer function */
    lunr.hi.wordCharacters = "\u0900-\u0903\u0904-\u090f\u0910-\u091f\u0920-\u092f\u0930-\u093f\u0940-\u094f\u0950-\u095f\u0960-\u096f\u0970-\u097fa-zA-Zａ-ｚＡ-Ｚ0-9０-９";
    // lunr.hi.wordCharacters = "ऀँंःऄअआइईउऊऋऌऍऎएऐऑऒओऔकखगघङचछजझञटठडढणतथदधनऩपफबभमयरऱलळऴवशषसहऺऻ़ऽािीुूृॄॅॆेैॉॊोौ्ॎॏॐ॒॑॓॔ॕॖॗक़ख़ग़ज़ड़ढ़फ़य़ॠॡॢॣ।॥०१२३४५६७८९॰ॱॲॳॴॵॶॷॸॹॺॻॼॽॾॿa-zA-Zａ-ｚＡ-Ｚ0-9０-９";
    lunr.hi.trimmer = lunr.trimmerSupport.generateTrimmer(lunr.hi.wordCharacters);

    lunr.Pipeline.registerFunction(lunr.hi.trimmer, 'trimmer-hi');
    /* lunr stop word filter */
    lunr.hi.stopWordFilter = lunr.generateStopWordFilter(
      'अत अपना अपनी अपने अभी अंदर आदि आप इत्यादि इन इनका इन्हीं इन्हें इन्हों इस इसका इसकी इसके इसमें इसी इसे उन उनका उनकी उनके उनको उन्हीं उन्हें उन्हों उस उसके उसी उसे एक एवं एस ऐसे और कई कर करता करते करना करने करें कहते कहा का काफ़ी कि कितना किन्हें किन्हों किया किर किस किसी किसे की कुछ कुल के को कोई कौन कौनसा गया घर जब जहाँ जा जितना जिन जिन्हें जिन्हों जिस जिसे जीधर जैसा जैसे जो तक तब तरह तिन तिन्हें तिन्हों तिस तिसे तो था थी थे दबारा दिया दुसरा दूसरे दो द्वारा न नके नहीं ना निहायत नीचे ने पर पहले पूरा पे फिर बनी बही बहुत बाद बाला बिलकुल भी भीतर मगर मानो मे में यदि यह यहाँ यही या यिह ये रखें रहा रहे ऱ्वासा लिए लिये लेकिन व वग़ैरह वर्ग वह वहाँ वहीं वाले वुह वे वो सकता सकते सबसे सभी साथ साबुत साभ सारा से सो संग ही हुआ हुई हुए है हैं हो होता होती होते होना होने'.split(' '));
    /* lunr stemmer function */
    lunr.hi.stemmer = (function() {

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
    lunr.hi.tokenizer = function(obj) {
      if (!arguments.length || obj == null || obj == undefined) return []
      if (Array.isArray(obj)) return obj.map(function(t) {
        return isLunr2 ? new lunr.Token(t.toLowerCase()) : t.toLowerCase()
      });

      var str = obj.toString().toLowerCase().replace(/^\s+/, '');
      return segmenter.cut(str).split('|');
    }

    lunr.Pipeline.registerFunction(lunr.hi.stemmer, 'stemmer-hi');
    lunr.Pipeline.registerFunction(lunr.hi.stopWordFilter, 'stopWordFilter-hi');

  };
}))