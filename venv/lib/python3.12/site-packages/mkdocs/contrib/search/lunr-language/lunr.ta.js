/*!
 * Lunr languages, `Tamil` language
 * https://github.com/tvmani/lunr-languages
 *
 * Copyright 2021, Manikandan Venkatasubban
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
    lunr.ta = function() {
      this.pipeline.reset();
      this.pipeline.add(
        lunr.ta.trimmer,
        lunr.ta.stopWordFilter,
        lunr.ta.stemmer
      );

      // change the tokenizer for japanese one
      // if (isLunr2) { // for lunr version 2.0.0
      //   this.tokenizer = lunr.ta.tokenizer;
      // } else {
      //   if (lunr.tokenizer) { // for lunr version 0.6.0
      //     lunr.tokenizer = lunr.ta.tokenizer;
      //   }
      //   if (this.tokenizerFn) { // for lunr version 0.7.0 -> 1.0.0
      //     this.tokenizerFn = lunr.ta.tokenizer;
      //   }
      // }

      if (this.searchPipeline) {
        this.searchPipeline.reset();
        this.searchPipeline.add(lunr.ta.stemmer)
      }
    };

    /* lunr trimmer function */
    lunr.ta.wordCharacters = "\u0b80-\u0b89\u0b8a-\u0b8f\u0b90-\u0b99\u0b9a-\u0b9f\u0ba0-\u0ba9\u0baa-\u0baf\u0bb0-\u0bb9\u0bba-\u0bbf\u0bc0-\u0bc9\u0bca-\u0bcf\u0bd0-\u0bd9\u0bda-\u0bdf\u0be0-\u0be9\u0bea-\u0bef\u0bf0-\u0bf9\u0bfa-\u0bffa-zA-Zａ-ｚＡ-Ｚ0-9０-９";

    lunr.ta.trimmer = lunr.trimmerSupport.generateTrimmer(lunr.ta.wordCharacters);

    lunr.Pipeline.registerFunction(lunr.ta.trimmer, 'trimmer-ta');
    /* lunr stop word filter */
    lunr.ta.stopWordFilter = lunr.generateStopWordFilter(
      'அங்கு அங்கே அது அதை அந்த அவர் அவர்கள் அவள் அவன் அவை ஆக ஆகவே ஆகையால் ஆதலால் ஆதலினால் ஆனாலும் ஆனால் இங்கு இங்கே இது இதை இந்த இப்படி இவர் இவர்கள் இவள் இவன் இவை இவ்வளவு உனக்கு உனது உன் உன்னால் எங்கு எங்கே எது எதை எந்த எப்படி எவர் எவர்கள் எவள் எவன் எவை எவ்வளவு எனக்கு எனது எனவே என் என்ன என்னால் ஏது ஏன் தனது தன்னால் தானே தான் நாங்கள் நாம் நான் நீ நீங்கள்'.split(' '));
    /* lunr stemmer function */
    lunr.ta.stemmer = (function() {

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
    lunr.ta.tokenizer = function(obj) {
      if (!arguments.length || obj == null || obj == undefined) return []
      if (Array.isArray(obj)) return obj.map(function(t) {
        return isLunr2 ? new lunr.Token(t.toLowerCase()) : t.toLowerCase()
      });

      var str = obj.toString().toLowerCase().replace(/^\s+/, '');
      return segmenter.cut(str).split('|');
    }

    lunr.Pipeline.registerFunction(lunr.ta.stemmer, 'stemmer-ta');
    lunr.Pipeline.registerFunction(lunr.ta.stopWordFilter, 'stopWordFilter-ta');

  };
}))